from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CacheStats:
    """Snapshot of the five measures the sprint asks for ("ratio de
    hit, ratio de miss, taille, expiration, évictions") for one named
    cache."""

    cache_name: str
    hits: int
    misses: int
    evictions: int
    expirations: int
    size: int
    hit_ratio: float
    miss_ratio: float
