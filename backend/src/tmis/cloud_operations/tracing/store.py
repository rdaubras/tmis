from tmis.cloud_operations.tracing.schemas import Span


class InMemorySpanStore:
    def __init__(self) -> None:
        self._spans: dict[str, Span] = {}

    def save(self, span: Span) -> None:
        self._spans[span.id] = span

    def get(self, span_id: str) -> Span | None:
        return self._spans.get(span_id)

    def list_for_trace(self, trace_id: str) -> list[Span]:
        return sorted(
            (s for s in self._spans.values() if s.trace_id == trace_id),
            key=lambda s: s.started_at,
        )
