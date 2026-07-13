from typing import Protocol

from tmis.cloud_operations.tracing.schemas import Span


class SpanStorePort(Protocol):
    def save(self, span: Span) -> None: ...

    def get(self, span_id: str) -> Span | None: ...

    def list_for_trace(self, trace_id: str) -> list[Span]: ...
