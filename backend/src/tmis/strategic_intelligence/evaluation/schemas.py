from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class StrategyGenerationMetrics:
    """Operational telemetry about strategy generation itself — not a
    business judgment about the strategies produced. Mirrors
    `ai_governance.evaluation.GovernanceRunMetrics`'s role."""

    case_id: str
    strategy_count: int
    duration_ms: float
    playbooks_reused: int
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
