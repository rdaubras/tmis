from datetime import UTC, datetime, timedelta

from tmis.cloud_operations.logging.engine import LoggingGovernanceEngine
from tmis.cloud_operations.logging.schemas import LogRetentionCategory
from tmis.cloud_operations.logging.store import InMemoryLogRetentionPolicyStore
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.telemetry.engine import TelemetryEngine
from tmis.cloud_operations.telemetry.store import InMemoryTelemetryEventStore
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.cloud_operations.tracing.schemas import SpanKind
from tmis.cloud_operations.tracing.store import InMemorySpanStore
from tmis.platform.metrics.registry import MetricsRegistry


def _metrics_engine() -> MetricsEngine:
    return MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())


def test_metrics_engine_historizes_events_and_computes_average() -> None:
    engine = _metrics_engine()
    engine.record(MetricCategory.RESPONSE_TIME, "api", 100.0, firm_id="firm-1")
    engine.record(MetricCategory.RESPONSE_TIME, "api", 200.0, firm_id="firm-1")
    engine.record(MetricCategory.RESPONSE_TIME, "api", 999.0, firm_id="firm-2")

    history = engine.history_for_category(MetricCategory.RESPONSE_TIME, "firm-1")
    assert len(history) == 2
    assert engine.average(MetricCategory.RESPONSE_TIME, "firm-1") == 150.0


def test_metrics_engine_exposes_prometheus_exposition_format() -> None:
    engine = _metrics_engine()
    engine.record(MetricCategory.ERRORS, "workflow.timeout", 1.0)
    rendered = engine.render_prometheus()
    assert "workflow_timeout" in rendered or "errors" in rendered


def test_logging_governance_redacts_and_tracks_retention() -> None:
    engine = LoggingGovernanceEngine(InMemoryLogRetentionPolicyStore())
    redacted = engine.redact({"password": "secret", "message": "login"})
    assert redacted.get("password") != "secret"

    assert engine.retention_for(LogRetentionCategory.AUDIT) == 2_555
    engine.set_retention(LogRetentionCategory.AUDIT, 30)
    assert engine.retention_for(LogRetentionCategory.AUDIT) == 30

    old = datetime.now(UTC) - timedelta(days=31)
    assert engine.is_expired(LogRetentionCategory.AUDIT, old) is True
    assert engine.is_expired(LogRetentionCategory.AUDIT, datetime.now(UTC)) is False


def test_telemetry_engine_bridges_metrics_tracing_and_events() -> None:
    metrics = _metrics_engine()
    tracing = TracingEngine(InMemorySpanStore())
    telemetry = TelemetryEngine(metrics, tracing, InMemoryTelemetryEventStore())

    telemetry.record_metric(MetricCategory.AI_CALL_DURATION, "gpt-4o", 42.0, firm_id="firm-1")
    assert metrics.average(MetricCategory.AI_CALL_DURATION, "firm-1") == 42.0

    span = telemetry.start_span("trace-1", SpanKind.AI_FABRIC, "route")
    telemetry.end_span(span.id)
    assert tracing.trace("trace-1")[0].status.value == "ok"

    event = telemetry.emit_event("model.selected", firm_id="firm-1", payload={"model": "gpt-4o"})
    assert event in telemetry.events_for_firm("firm-1")
