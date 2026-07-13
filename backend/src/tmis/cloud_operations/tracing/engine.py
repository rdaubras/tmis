from datetime import UTC, datetime

from tmis.cloud_operations.tracing.ports import SpanStorePort
from tmis.cloud_operations.tracing.schemas import Span, SpanKind, SpanStatus, new_span_id


class UnknownSpanError(KeyError):
    pass


class TracingEngine:
    """Distributed tracing across the sprint's request path
    (Utilisateur → API → Workflow → AI Fabric → Agents → Knowledge
    Engine → Connecteurs → Réponse). Every span shares the trace id
    already carried by `request.state.trace_id` (see `tracing.
    schemas.Span` docstring) — this engine only tracks the tree of
    spans *within* one trace, never mints a new correlation scheme."""

    def __init__(self, store: SpanStorePort) -> None:
        self._store = store

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
        span = Span(
            id=new_span_id(),
            trace_id=trace_id,
            kind=kind,
            name=name,
            parent_span_id=parent_span_id,
            firm_id=firm_id,
            attributes=attributes or {},
        )
        self._store.save(span)
        return span

    def end_span(self, span_id: str, *, status: SpanStatus = SpanStatus.OK) -> Span:
        span = self._store.get(span_id)
        if span is None:
            raise UnknownSpanError(span_id)
        span.ended_at = datetime.now(UTC)
        span.status = status
        self._store.save(span)
        return span

    def trace(self, trace_id: str) -> list[Span]:
        return self._store.list_for_trace(trace_id)

    def trace_duration_ms(self, trace_id: str) -> float | None:
        spans = self.trace(trace_id)
        if not spans:
            return None
        started = min(s.started_at for s in spans)
        ended = [s.ended_at for s in spans if s.ended_at is not None]
        if not ended:
            return None
        return (max(ended) - started).total_seconds() * 1000
