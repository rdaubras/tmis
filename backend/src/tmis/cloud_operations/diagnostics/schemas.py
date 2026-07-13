from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cloud_operations.error_tracking.schemas import ErrorEvent
from tmis.cloud_operations.tracing.schemas import Span
from tmis.platform.health.schemas import SystemHealth


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """A one-shot correlation of health, performance, recent errors,
    and (optionally) one request's trace — composes `platform.health`,
    `cloud_operations.performance`, `cloud_operations.error_tracking`,
    and `cloud_operations.tracing` rather than re-deriving any of
    them, so an operator can answer "why is this slow / broken" from
    one call instead of four."""

    health: SystemHealth
    response_time_avg_ms: float
    response_time_p95_ms: float
    recent_errors: list[ErrorEvent]
    trace: list[Span] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
