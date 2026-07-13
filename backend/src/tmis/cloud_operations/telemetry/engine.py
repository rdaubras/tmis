from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory, MetricEvent
from tmis.cloud_operations.telemetry.ports import TelemetryEventStorePort
from tmis.cloud_operations.telemetry.schemas import TelemetryEvent, new_telemetry_event_id
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.cloud_operations.tracing.schemas import Span, SpanKind, SpanStatus


class TelemetryEngine:
    """The common instrumentation facade the sprint asks every TMIS
    module to publish through ("métriques, traces, événements"),
    shaped after OpenTelemetry's own API surface
    (record_metric/start_span/end_span/emit_event) so it can stay
    "indépendant des outils de supervision" (sprint requirement):
    TMIS has no OpenTelemetry SDK dependency today (see
    docs/49-guide-supervision.md — the metrics registry is
    hand-rolled, deliberately, to avoid adding one for a mock-scope
    endpoint), so this facade is backed by `cloud_operations.metrics.
    MetricsEngine` and `cloud_operations.tracing.TracingEngine`
    in-process. A real OpenTelemetry SDK/exporter can be substituted
    behind this exact interface later without any calling module
    changing a single line — that substitution is out of scope for
    this sprint (see docs/126-guide-opentelemetry.md)."""

    def __init__(
        self,
        metrics: MetricsEngine,
        tracing: TracingEngine,
        events: TelemetryEventStorePort,
    ) -> None:
        self._metrics = metrics
        self._tracing = tracing
        self._events = events

    def record_metric(
        self,
        category: MetricCategory,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
        firm_id: str | None = None,
    ) -> MetricEvent:
        return self._metrics.record(category, name, value, labels=labels, firm_id=firm_id)

    def start_span(
        self,
        trace_id: str,
        kind: SpanKind,
        name: str,
        *,
        parent_span_id: str | None = None,
        firm_id: str | None = None,
        attributes: dict[str, str] | None = None,
    ) -> Span:
        return self._tracing.start_span(
            trace_id,
            kind,
            name,
            parent_span_id=parent_span_id,
            firm_id=firm_id,
            attributes=attributes,
        )

    def end_span(self, span_id: str, *, status: SpanStatus = SpanStatus.OK) -> Span:
        return self._tracing.end_span(span_id, status=status)

    def emit_event(
        self, name: str, *, firm_id: str | None = None, payload: dict[str, str] | None = None
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            id=new_telemetry_event_id(), name=name, firm_id=firm_id, payload=payload or {}
        )
        self._events.save(event)
        return event

    def events_for_firm(self, firm_id: str) -> list[TelemetryEvent]:
        return self._events.list_for_firm(firm_id)
