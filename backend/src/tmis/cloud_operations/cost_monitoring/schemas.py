from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class CostMonitoringSnapshot:
    """Cost breakdown for one firm. Grouped by `model` (the closest
    available dimension on `platform.cost_control.schemas.CostEntry`
    — that schema has no `agent_id` field today, so "coût par agent"
    is not yet derivable; documented as a future `CostEntry` field
    rather than approximated here) and by `user_id`."""

    firm_id: str
    total_cost_usd: float
    cost_by_model: dict[str, float]
    cost_by_user: dict[str, float]
    cache_hit_rate: float
    breach_count: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
