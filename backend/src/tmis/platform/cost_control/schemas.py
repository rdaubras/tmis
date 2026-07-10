from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CostEntry:
    """One AI call's cost, attributed to a user/case/workflow (see
    docs/50-guide-performance.md — Cost Control). A cache hit costs
    nothing — no fresh generation happened — but is still recorded, so
    `cache_hit_rate` can be measured."""

    id: str
    firm_id: str
    user_id: str
    case_id: str | None
    workflow_id: str | None
    provider: str
    model: str
    token_count: int
    cost_usd: float
    cache_hit: bool
    recorded_at: datetime


@dataclass(frozen=True, slots=True)
class AlertThreshold:
    """A cost ceiling for one scope (a firm or a user) over a rolling
    period — see docs/50-guide-performance.md — Seuils d'alerte."""

    scope: str
    scope_id: str
    max_cost_usd: float
    period_days: int = 30


@dataclass(frozen=True, slots=True)
class CostBreach:
    threshold: AlertThreshold
    current_cost_usd: float
    checked_at: datetime
