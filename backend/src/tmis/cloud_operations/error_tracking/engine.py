from tmis.cloud_operations.error_tracking.ports import ErrorEventStorePort
from tmis.cloud_operations.error_tracking.schemas import (
    ErrorEvent,
    ErrorSeverity,
    new_error_event_id,
)
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory


class ErrorTrackingEngine:
    """Cross-cutting error aggregation — any module (workflow engine,
    AI Fabric, connectors, ...) reports its exceptions here through one
    generic API rather than this engine reimplementing each module's
    own error model; every error also increments the shared `ERRORS`
    metric category via `cloud_operations.metrics.MetricsEngine`."""

    def __init__(self, store: ErrorEventStorePort, metrics: MetricsEngine) -> None:
        self._store = store
        self._metrics = metrics

    def record(
        self,
        source: str,
        error_type: str,
        message: str,
        *,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        firm_id: str | None = None,
    ) -> ErrorEvent:
        event = ErrorEvent(
            id=new_error_event_id(),
            source=source,
            error_type=error_type,
            message=message,
            severity=severity,
            firm_id=firm_id,
        )
        self._store.save(event)
        self._metrics.record(MetricCategory.ERRORS, f"{source}.{error_type}", 1.0, firm_id=firm_id)
        return event

    def recent(self, limit: int = 50) -> list[ErrorEvent]:
        return self._store.list_recent(limit)

    def error_rate_by_source(self, source: str) -> int:
        return len(self._store.list_for_source(source))
