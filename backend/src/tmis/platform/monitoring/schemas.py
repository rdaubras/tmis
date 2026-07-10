from dataclasses import dataclass, field
from datetime import datetime

from tmis.platform.health.schemas import SystemHealth


@dataclass(frozen=True, slots=True)
class SupervisionDashboard:
    """The one-screen operational view (see docs/49-guide-supervision.md
    — Tableaux de bord de supervision): dependency health plus a
    handful of headline metrics. Deliberately not a copy of everything
    in `/platform/metrics` — a dashboard is curated, the metrics
    endpoint is exhaustive."""

    system_health: SystemHealth
    total_requests: float
    ai_cost_usd_total: float
    computed_at: datetime
    extra: dict[str, float] = field(default_factory=dict)
