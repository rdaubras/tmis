import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cloud_operations.sla.schemas import SLAMetricType


def new_slo_target_id() -> str:
    return f"slot-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class SLOTarget:
    """An SLO is an internal objective — usually stricter than the
    contractual SLA (`sla.schemas.SLATarget`) — used to trigger
    proactive action *before* an SLA is actually breached. Same
    metric vocabulary (`SLAMetricType`), reused rather than a second
    enum, since the underlying measurement is identical; only the
    target's strictness and consequence differ."""

    id: str
    service_name: str
    metric_type: SLAMetricType
    objective_value: float


@dataclass(frozen=True, slots=True)
class SLOStatus:
    """`error_budget_remaining_percent` is only meaningful for
    "higher is better" metrics (availability/success_rate) — the
    error budget is "how much failure is still allowed before the
    objective is breached". For "lower is better" metrics (latency/
    restoration_time) it is always 100 when met, 0 when not — there
    is no partial-budget concept for a single-sample threshold."""

    service_name: str
    metric_type: SLAMetricType
    objective_value: float
    actual_value: float
    error_budget_remaining_percent: float
    at_risk: bool
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
