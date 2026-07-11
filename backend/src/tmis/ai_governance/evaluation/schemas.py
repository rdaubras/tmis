from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class GovernanceRunMetrics:
    """Operational telemetry about the governance platform's own
    performance — not a business judgment about the production it
    governed. Mirrors `tmis.ai.evaluation.metrics.EvaluationMetrics`'s
    role for `TMISKernel`."""

    production_id: str
    duration_ms: float
    risk_count: int
    finding_count: int
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
