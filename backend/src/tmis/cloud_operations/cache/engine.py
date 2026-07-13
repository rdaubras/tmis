from dataclasses import dataclass

from tmis.cloud_operations.cache.schemas import CacheStats
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory


@dataclass
class _RawCacheCounters:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    size: int = 0


class CacheObservabilityEngine:
    """Instrumentation wrapper layer — no existing cache implementation
    (`ai.cache.InMemoryCache`, `ai_fabric.cache.ResponseCache`) tracks
    hit/miss/eviction/expiration/size statistics, confirmed by direct
    inspection. Rather than modifying every cache class, callers report
    their events here alongside their normal get/set/evict logic; this
    engine both keeps a running per-cache snapshot and forwards every
    event into `cloud_operations.metrics.MetricsEngine` so cache
    behaviour is also historisée like every other measurement."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics
        self._counters: dict[str, _RawCacheCounters] = {}

    def _counters_for(self, cache_name: str) -> _RawCacheCounters:
        return self._counters.setdefault(cache_name, _RawCacheCounters())

    def record_hit(self, cache_name: str, firm_id: str | None = None) -> None:
        self._counters_for(cache_name).hits += 1
        self._metrics.record(MetricCategory.CACHE, f"{cache_name}.hit", 1.0, firm_id=firm_id)

    def record_miss(self, cache_name: str, firm_id: str | None = None) -> None:
        self._counters_for(cache_name).misses += 1
        self._metrics.record(MetricCategory.CACHE, f"{cache_name}.miss", 1.0, firm_id=firm_id)

    def record_eviction(self, cache_name: str, firm_id: str | None = None) -> None:
        self._counters_for(cache_name).evictions += 1
        self._metrics.record(MetricCategory.CACHE, f"{cache_name}.eviction", 1.0, firm_id=firm_id)

    def record_expiration(self, cache_name: str, firm_id: str | None = None) -> None:
        self._counters_for(cache_name).expirations += 1
        self._metrics.record(MetricCategory.CACHE, f"{cache_name}.expiration", 1.0, firm_id=firm_id)

    def set_size(self, cache_name: str, size: int, firm_id: str | None = None) -> None:
        self._counters_for(cache_name).size = size
        self._metrics.record(
            MetricCategory.CACHE, f"{cache_name}.size", float(size), firm_id=firm_id
        )

    def stats(self, cache_name: str) -> CacheStats:
        counters = self._counters_for(cache_name)
        total = counters.hits + counters.misses
        hit_ratio = counters.hits / total if total else 0.0
        miss_ratio = counters.misses / total if total else 0.0
        return CacheStats(
            cache_name=cache_name,
            hits=counters.hits,
            misses=counters.misses,
            evictions=counters.evictions,
            expirations=counters.expirations,
            size=counters.size,
            hit_ratio=hit_ratio,
            miss_ratio=miss_ratio,
        )
