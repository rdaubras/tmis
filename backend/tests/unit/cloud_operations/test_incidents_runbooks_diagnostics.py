import pytest

from tmis.cloud_operations.diagnostics.engine import DiagnosticsEngine
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.error_tracking.store import InMemoryErrorEventStore
from tmis.cloud_operations.incident_management.engine import (
    IncidentManagementEngine,
    UnknownIncidentError,
)
from tmis.cloud_operations.incident_management.schemas import IncidentSeverity, IncidentStatus
from tmis.cloud_operations.incident_management.store import (
    InMemoryIncidentStore,
    InMemoryIncidentUpdateStore,
)
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.runbooks.engine import RunbooksEngine
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.cloud_operations.tracing.schemas import SpanKind
from tmis.cloud_operations.tracing.store import InMemorySpanStore
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.metrics.registry import MetricsRegistry


def _incident_engine() -> IncidentManagementEngine:
    return IncidentManagementEngine(InMemoryIncidentStore(), InMemoryIncidentUpdateStore())


def test_incident_lifecycle_open_track_resolve_post_mortem() -> None:
    engine = _incident_engine()
    incident = engine.open_incident(
        "OpenAI outage", "GPT-4 calls failing", IncidentSeverity.HIGH, firm_id="firm-1"
    )
    assert incident.status is IncidentStatus.OPEN

    engine.track(incident.id, "Confirmed provider outage via status page", author="ops-bot")
    assert engine.timeline(incident.id)[0].author == "ops-bot"

    resolved = engine.resolve(incident.id)
    assert resolved.status is IncidentStatus.RESOLVED

    report = engine.record_post_mortem(
        incident.id,
        root_cause="Provider outage",
        impact="5min elevated latency",
        resolution="Failover to backup model",
        action_items=["Add second provider"],
    )
    assert report.duration_minutes >= 0
    assert engine.open_incidents("firm-1") == []


def test_incident_engine_raises_on_unknown_incident() -> None:
    engine = _incident_engine()
    with pytest.raises(UnknownIncidentError):
        engine.resolve("does-not-exist")


def test_runbooks_engine_seeds_default_procedures_and_finds_by_tag() -> None:
    engine = RunbooksEngine()
    runbook = engine.get("ai-provider-unavailable")
    assert runbook is not None
    assert len(runbook.steps) == 5
    assert len(engine.find_by_tag("ai_fabric")) == 1
    assert len(engine.list_all()) == 5


def test_diagnostics_engine_composes_health_performance_errors_and_trace() -> None:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    metrics.record(MetricCategory.RESPONSE_TIME, "api", 120.0)
    metrics.record(MetricCategory.RESPONSE_TIME, "api", 80.0)

    errors = ErrorTrackingEngine(InMemoryErrorEventStore(), metrics)
    errors.record("workflow_engine", "timeout", "step timed out")

    tracing = TracingEngine(InMemorySpanStore())
    span = tracing.start_span("trace-1", SpanKind.API, "GET /cases")
    tracing.end_span(span.id)

    diagnostics = DiagnosticsEngine(
        HealthCheckEngine(), PerformanceEngine(metrics), errors, tracing
    )
    report = diagnostics.diagnose(trace_id="trace-1")

    assert report.response_time_avg_ms == 100.0
    assert len(report.recent_errors) == 1
    assert len(report.trace) == 1
