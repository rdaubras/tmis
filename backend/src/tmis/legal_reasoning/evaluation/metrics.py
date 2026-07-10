from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningMetrics:
    """Metrics for one reasoning run (see docs/25-legal-reasoning.md —
    Observabilité): duration, modules exercised, average confidence,
    hypothesis and conflict counts."""

    session_id: str
    duration_ms: float
    modules_used: tuple[str, ...]
    average_confidence: float
    hypothesis_count: int
    argument_count: int
    counter_argument_count: int
    conflict_count: int
