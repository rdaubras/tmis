from functools import lru_cache
from typing import TYPE_CHECKING

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.cache.ports import CachePort
from tmis.ai.cache.redis_cache import RedisCache
from tmis.core.config import get_settings
from tmis.core.logging import get_logger

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = get_logger(__name__)

_PING_TIMEOUT_SECONDS = 0.5


def _redis_reachable(redis_url: str) -> bool:
    """A bounded, synchronous `PING` — the one deliberate exception to
    this repo's usual "never dial the backend at construction, only
    decide whether to" rule (see `tmis.ai.rag.adapters.
    qdrant_client_factory.get_qdrant_client`). `CachePort` sits on the
    hot path of nearly every Kernel call, connector search, and LRE cache
    layer, so silently handing every one of them a backend that will
    only fail on first real use is worse here than the short, bounded
    cost of checking once at startup (see docs/155-architecture-cache-
    production.md for the tradeoff).
    """
    import redis  # deferred: only the sync client is needed for this one-off probe

    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=_PING_TIMEOUT_SECONDS,
            socket_timeout=_PING_TIMEOUT_SECONDS,
        )
        try:
            return bool(client.ping())
        finally:
            client.close()
    except Exception as exc:  # noqa: BLE001 — an unreachable/misconfigured Redis must never crash startup
        logger.warning("cache.redis_unreachable", redis_url=redis_url, error=str(exc))
        return False


@lru_cache
def _shared_redis_client() -> "Redis | None":
    """Process-wide async Redis client, built at most once — the one
    Redis *connection* this factory owns (Celery's broker/backend in
    `tmis.core.tasks.celery_app` manages its own connection independently,
    since Celery owns that lifecycle end-to-end; this is the one shared by
    everything that goes through `CachePort`). Returns `None` if Redis
    never answers a `PING`, so every caller of `make_cache()` degrades the
    same way without repeating the probe.
    """
    settings = get_settings()
    if not _redis_reachable(settings.redis_url):
        return None

    from redis.asyncio import Redis  # deferred: only needed once Redis is confirmed reachable

    logger.info("cache.backend_selected", backend="redis", redis_url=settings.redis_url)
    return Redis.from_url(settings.redis_url)  # type: ignore[no-any-return]


def get_shared_redis_client() -> "Redis | None":
    """Public accessor for the one process-wide Redis client this factory
    owns (see `_shared_redis_client`), reused by
    `tmis.ai.memory.factory.make_memory_store()` so the whole repo shares
    a single Redis connection mechanism instead of each factory dialing
    its own."""
    return _shared_redis_client()


def make_cache() -> CachePort:
    """Single composition point deciding `InMemoryCache` vs `RedisCache`
    (see docs/155-architecture-cache-production.md), reused by every
    hardcoded cache default in the repo (`TMISKernel`, `BaseConnectorPlugin`,
    `ai_fabric.bootstrap.get_response_cache`) instead of each guessing
    independently.

    Defaults to a fresh `InMemoryCache` — dev/tests keep working with zero
    external dependency and the exact isolation each caller already had
    (one private dict per instance, never shared). Only switches to
    `RedisCache` when `redis_url` actually answers a `PING` (checked once
    per process, see `_shared_redis_client`); any failure (down,
    misconfigured, network partition) degrades to `InMemoryCache` rather
    than ever failing startup. Every `RedisCache` instance this returns
    shares the one underlying client/connection pool.
    """
    client = _shared_redis_client()
    if client is None:
        return InMemoryCache()
    return RedisCache(client)
