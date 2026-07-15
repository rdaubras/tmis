from tmis.ai.cache.factory import get_shared_redis_client
from tmis.ai.memory.in_memory_store import InMemoryStore
from tmis.ai.memory.ports import MemoryStorePort
from tmis.ai.memory.redis_store import RedisMemoryStore
from tmis.core.logging import get_logger

logger = get_logger(__name__)


def make_memory_store() -> MemoryStorePort:
    """Single composition point deciding `RedisMemoryStore` vs
    `InMemoryStore`, the same patron as `tmis.ai.cache.factory.make_cache`
    (Sprint 28) reproduced for the memory store — replaces the hardcoded
    `InMemoryStore()` default in `TMISKernel.__init__`.

    Reuses `tmis.ai.cache.factory.get_shared_redis_client()` — the one
    process-wide Redis client the repo owns — rather than dialing a
    second connection: `RedisMemoryStore` and `RedisCache` end up sharing
    the exact same client/connection pool whenever Redis is configured
    and reachable. Defaults to a fresh `InMemoryStore()` (dev/tests, zero
    external dependency) whenever that client is `None` — never fails
    startup if Redis is absent or unreachable.
    """
    client = get_shared_redis_client()
    if client is None:
        return InMemoryStore()
    logger.info("memory.backend_selected", backend="redis")
    return RedisMemoryStore(client)
