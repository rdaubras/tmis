from tmis.cloud_operations.diagnostics.schemas import DiagnosticReport
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.platform.health.engine import HealthCheckEngine


class DiagnosticsEngine:
    """Composition-only diagnostics facade — pulls a `SystemHealth`
    snapshot, a `PerformanceSnapshot`, recent tracked errors, and
    (when given a `trace_id`) the full span tree for one request into
    a single `DiagnosticReport`, without owning any state itself."""

    def __init__(
        self,
        health: HealthCheckEngine,
        performance: PerformanceEngine,
        errors: ErrorTrackingEngine,
        tracing: TracingEngine,
    ) -> None:
        self._health = health
        self._performance = performance
        self._errors = errors
        self._tracing = tracing

    def diagnose(self, firm_id: str | None = None, trace_id: str | None = None) -> DiagnosticReport:
        health = self._health.readiness()
        performance = self._performance.snapshot(firm_id)
        recent_errors = self._errors.recent(limit=20)
        trace = self._tracing.trace(trace_id) if trace_id else []
        return DiagnosticReport(
            health=health,
            response_time_avg_ms=performance.response_time_avg_ms,
            response_time_p95_ms=performance.response_time_p95_ms,
            recent_errors=recent_errors,
            trace=trace,
        )
