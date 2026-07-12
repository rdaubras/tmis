import base64
import zlib
from collections.abc import Awaitable, Callable

from tmis.ai.cache.ports import CachePort
from tmis.runtime_platform.distributed_cache.schemas import CacheUsageStats

_COMPRESS_PREFIX = "z:"
_RAW_PREFIX = "r:"
_COMPRESS_MIN_LENGTH = 256


class DistributedCacheEngine:
    """Extends `ai.cache.CachePort` (already Redis-backed via
    `RedisCache` — the one genuinely distributed cache confirmed by
    the Sprint 23 Phase 1 audit, wired to the `redis` service in
    `docker-compose.yml`) rather than inventing a second cache
    abstraction. Adds: application-level invalidation broadcast (for
    in-process listeners that need to know a key changed, on top of
    Redis's own cross-process consistency), warming, value
    compression, adaptive TTL, and usage statistics — none of which
    `CachePort` or its existing callers (`legal_research.cache.
    ResearchCache`, `ai_fabric.cache.ResponseCache`) implement."""

    def __init__(self, cache: CachePort) -> None:
        self._cache = cache
        self._stats = CacheUsageStats()
        self._access_counts: dict[str, int] = {}
        self._listeners: list[Callable[[str], None]] = []

    async def get(self, key: str) -> str | None:
        raw = await self._cache.get(key)
        if raw is None:
            self._stats.misses += 1
            return None
        self._stats.hits += 1
        self._access_counts[key] = self._access_counts.get(key, 0) + 1
        return _decode(raw)

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        encoded, saved_bytes = _encode(value)
        self._stats.bytes_saved_by_compression += saved_bytes
        await self._cache.set(key, encoded, ttl_seconds=self._smart_ttl(key, ttl_seconds))
        self._stats.sets += 1

    async def delete(self, key: str) -> None:
        """Passthrough so `DistributedCacheEngine` fully satisfies
        `CachePort` and can be substituted anywhere a plain cache is
        expected — see the Sprint 23 migration of `legal_research.
        bootstrap.get_research_orchestrator`, which now wraps the
        Kernel's cache with this engine instead of using it raw."""
        await self._cache.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._cache.exists(key)

    def register_invalidation_listener(self, listener: Callable[[str], None]) -> None:
        self._listeners.append(listener)

    async def invalidate(self, key: str) -> None:
        """Deletes the key and notifies every registered listener —
        the "distributed invalidation" broadcast for in-process
        readers that cached a copy of this value themselves (e.g. a
        three-layer cache like `legal_research.cache.ResearchCache`)
        and need to drop it too, beyond what Redis's own shared
        storage already guarantees across processes."""
        await self._cache.delete(key)
        self._stats.invalidations += 1
        for listener in self._listeners:
            listener(key)

    async def warm(
        self,
        loaders: dict[str, Callable[[], Awaitable[str]]],
        *,
        ttl_seconds: int | None = None,
    ) -> int:
        """Pre-populates the given keys by calling each loader,
        skipping keys already present — used before an expected
        traffic spike (e.g. before a batch of firms' morning login)."""
        warmed = 0
        for key, loader in loaders.items():
            if await self._cache.exists(key):
                continue
            value = await loader()
            await self.set(key, value, ttl_seconds=ttl_seconds)
            warmed += 1
        self._stats.warmed_keys += warmed
        return warmed

    def _smart_ttl(self, key: str, ttl_seconds: int | None) -> int | None:
        """Heuristic, not machine learning: a key accessed often gets
        its TTL extended (up to 4x) on re-set, since a hot key is
        cheaper to keep warm than to keep recomputing — the
        "intelligent cache" behavior the sprint asks for."""
        if ttl_seconds is None:
            return None
        hits = self._access_counts.get(key, 0)
        multiplier = min(1 + hits // 5, 4)
        return ttl_seconds * multiplier

    @property
    def stats(self) -> CacheUsageStats:
        return self._stats


def _encode(value: str) -> tuple[str, int]:
    if len(value) < _COMPRESS_MIN_LENGTH:
        return _RAW_PREFIX + value, 0
    compressed = base64.b64encode(zlib.compress(value.encode("utf-8"))).decode("ascii")
    candidate = _COMPRESS_PREFIX + compressed
    if len(candidate) >= len(value):
        return _RAW_PREFIX + value, 0
    return candidate, len(value) - len(candidate)


def _decode(stored: str) -> str:
    if stored.startswith(_COMPRESS_PREFIX):
        payload = stored[len(_COMPRESS_PREFIX) :]
        return zlib.decompress(base64.b64decode(payload)).decode("utf-8")
    return stored[len(_RAW_PREFIX) :]
