from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StepMetric:
    """Timing/outcome of a single enrichment step, for one case update."""

    step: str
    duration_ms: float
    success: bool
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CaseUpdateMetrics:
    """Aggregated metrics for one full living-case update (see
    docs/19-case-intelligence.md — Observabilité)."""

    case_id: str
    document_id: str
    total_duration_ms: float
    step_metrics: tuple[StepMetric, ...] = field(default_factory=tuple)

    @property
    def error_count(self) -> int:
        return sum(1 for step in self.step_metrics if not step.success)
