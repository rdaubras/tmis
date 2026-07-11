from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResponseMetrics:
    """Deterministic, heuristic metrics computed on a raw model
    response — the shared measurement layer `critic/`, `comparison/`,
    and (later) `benchmark/` all build on rather than each
    reimplementing coherence/citation/contradiction detection."""

    length_words: int
    citation_count: int
    coherence_score: float
    contradiction_flags: tuple[str, ...] = field(default_factory=tuple)
