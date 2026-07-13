import pytest

from tmis.cloud_operations.alerting.engine import AlertingEngine
from tmis.cloud_operations.alerting.schemas import AlertComparison, AlertSeverity
from tmis.cloud_operations.alerting.store import InMemoryAlertEventStore, InMemoryAlertRuleStore
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.tracing.engine import TracingEngine, UnknownSpanError
from tmis.cloud_operations.tracing.schemas import SpanKind, SpanStatus
from tmis.cloud_operations.tracing.store import InMemorySpanStore
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.platform.metrics.registry import MetricsRegistry


def test_tracing_engine_builds_a_multi_hop_trace_under_one_trace_id() -> None:
    engine = TracingEngine(InMemorySpanStore())
    api_span = engine.start_span("trace-1", SpanKind.API, "GET /cases")
    workflow_span = engine.start_span(
        "trace-1", SpanKind.WORKFLOW, "run-workflow", parent_span_id=api_span.id
    )
    ai_span = engine.start_span(
        "trace-1", SpanKind.AI_FABRIC, "route-model", parent_span_id=workflow_span.id
    )
    engine.end_span(ai_span.id)
    engine.end_span(workflow_span.id)
    engine.end_span(api_span.id, status=SpanStatus.OK)

    spans = engine.trace("trace-1")
    assert len(spans) == 3
    assert {s.kind for s in spans} == {SpanKind.API, SpanKind.WORKFLOW, SpanKind.AI_FABRIC}
    assert workflow_span.parent_span_id == api_span.id
    assert ai_span.parent_span_id == workflow_span.id
    assert engine.trace_duration_ms("trace-1") is not None


def test_tracing_engine_rejects_unknown_span() -> None:
    engine = TracingEngine(InMemorySpanStore())
    with pytest.raises(UnknownSpanError):
        engine.end_span("does-not-exist")


def test_alerting_engine_fires_on_threshold_breach_and_notifies() -> None:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    engine = AlertingEngine(
        InMemoryAlertRuleStore(), InMemoryAlertEventStore(), metrics, NotificationEngine()
    )
    rule = engine.configure_rule(
        "high-latency",
        MetricCategory.RESPONSE_TIME,
        AlertComparison.GREATER_THAN,
        500.0,
        severity=AlertSeverity.CRITICAL,
        firm_id="firm-1",
        notify_recipient_id="user-1",
    )

    metrics.record(MetricCategory.RESPONSE_TIME, "api", 100.0, firm_id="firm-1")
    assert engine.evaluate(rule.id) is None

    metrics.record(MetricCategory.RESPONSE_TIME, "api", 900.0, firm_id="firm-1")
    fired = engine.evaluate(rule.id)
    assert fired is not None
    assert fired.severity == AlertSeverity.CRITICAL
    assert len(engine.history("firm-1")) == 1


def test_alerting_engine_evaluate_all_only_fires_active_rules() -> None:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    engine = AlertingEngine(InMemoryAlertRuleStore(), InMemoryAlertEventStore(), metrics)
    rule = engine.configure_rule(
        "high-errors", MetricCategory.ERRORS, AlertComparison.GREATER_THAN, 0.0, firm_id="firm-1"
    )
    metrics.record(MetricCategory.ERRORS, "workflow", 1.0, firm_id="firm-1")

    engine.deactivate_rule(rule.id)
    assert engine.evaluate_all("firm-1") == []
