from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchMetrics:
    """Metrics for one research run (see docs/21-legal-research.md —
    Évaluation): search time, source count, result quality proxies,
    duplicate rate, cache usage."""

    search_id: str
    query: str
    search_time_ms: float
    source_count: int
    result_count: int
    duplicate_rate: float
    cache_hit: bool
    connectors_used: tuple[str, ...]
