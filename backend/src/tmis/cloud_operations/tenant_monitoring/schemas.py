from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.business_platform.usage.schemas import UsageSnapshot


@dataclass(frozen=True, slots=True)
class TenantMonitoringSnapshot:
    """Per-firm dashboard — "activité, consommation, disponibilité,
    quotas, incidents" (sprint requirement) — a pure composition over
    `business_platform.analytics` (Sprint 20, activité/consommation),
    `business_platform.usage` (Sprint 20, quotas), and
    `cloud_operations.incident_management` (Sprint 21, incidents).
    "Disponibilité" is not included here: it has no firm-scoped
    meaning today (`platform.health` reports one platform-wide status,
    not a per-tenant SLA) — a genuine gap, not silently approximated,
    left for a future sprint once per-tenant SLA targets exist in
    `cloud_operations.sla`."""

    firm_id: str
    monthly_recurring_revenue_usd: float
    total_ai_cost_usd: float
    active_modules_count: int
    quota_usage: list[UsageSnapshot]
    open_incidents_count: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
