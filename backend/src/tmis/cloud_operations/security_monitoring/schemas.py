from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class SecurityMonitoringSnapshot:
    """Platform-wide security event aggregation — complements (never
    duplicates) `identity_platform.monitoring.IdentityMonitoringEngine.
    dashboard(firm_id)` (Sprint 19, per-firm) with a cross-tenant view
    composed directly over `identity_platform.security_events.
    SecurityEventBus.history`."""

    total_events: int
    events_by_type: dict[str, int]
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
