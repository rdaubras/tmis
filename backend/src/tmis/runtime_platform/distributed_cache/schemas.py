from dataclasses import dataclass


@dataclass(slots=True)
class CacheUsageStats:
    """Usage counters no existing cache in TMIS tracks today — `ai.
    cache.InMemoryCache`/`RedisCache` only implement get/set/delete/
    exists, with no hit/miss/warming/compression telemetry of their
    own (confirmed by the Sprint 23 Phase 1 audit; `cloud_operations.
    cache.CacheObservabilityEngine` tracks hit/miss but is a
    caller-reported wrapper, not integrated with `CachePort`)."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    warmed_keys: int = 0
    bytes_saved_by_compression: int = 0
