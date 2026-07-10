from dataclasses import dataclass

_DEFAULT_TTL_SECONDS: dict[str, int] = {
    "kernel_completion": 3600,
    "research_raw": 1800,
    "research_normalized": 3600,
    "research_ranked": 900,
}


@dataclass(frozen=True, slots=True)
class CachePolicy:
    resource_type: str
    ttl_seconds: int


class CachePolicyRegistry:
    """A TTL-per-resource-type policy layer sitting *above*
    `tmis.ai.cache.CachePort` (see docs/50-guide-performance.md —
    Cache): it does not reimplement caching, it just tells a caller
    what TTL to pass to `CachePort.set(..., ttl_seconds=...)` for a
    given kind of cached value, so that policy lives in one place
    instead of being a magic number scattered across call sites."""

    def __init__(self, defaults: dict[str, int] | None = None) -> None:
        self._ttls: dict[str, int] = dict(defaults or _DEFAULT_TTL_SECONDS)

    def set_ttl(self, resource_type: str, ttl_seconds: int) -> CachePolicy:
        self._ttls[resource_type] = ttl_seconds
        return CachePolicy(resource_type=resource_type, ttl_seconds=ttl_seconds)

    def get_ttl(self, resource_type: str, default: int = 300) -> int:
        return self._ttls.get(resource_type, default)
