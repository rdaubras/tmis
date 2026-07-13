from tmis.cloud_operations.security_monitoring.schemas import SecurityMonitoringSnapshot
from tmis.identity_platform.security_events.bus import SecurityEventBus


class SecurityMonitoringEngine:
    """Composes `identity_platform.security_events.SecurityEventBus`
    (Sprint 19) directly rather than a second security-event log."""

    def __init__(self, event_bus: SecurityEventBus) -> None:
        self._event_bus = event_bus

    def overview(self) -> SecurityMonitoringSnapshot:
        history = self._event_bus.history
        events_by_type: dict[str, int] = {}
        for event in history:
            events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
        return SecurityMonitoringSnapshot(total_events=len(history), events_by_type=events_by_type)
