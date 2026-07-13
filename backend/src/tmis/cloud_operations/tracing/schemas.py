import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SpanKind(StrEnum):
    """The eight stops of the sprint's request path diagram
    (Utilisateur → API → Workflow → AI Fabric → Agents → Knowledge
    Engine → Connecteurs → Réponse)."""

    API = "api"
    WORKFLOW = "workflow"
    AI_FABRIC = "ai_fabric"
    AGENT = "agent"
    KNOWLEDGE_ENGINE = "knowledge_engine"
    CONNECTOR = "connector"
    RESPONSE = "response"
    OTHER = "other"


class SpanStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


def new_span_id() -> str:
    return f"span-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Span:
    """One step of a distributed trace. `trace_id` is never generated
    here — it is always the same id `core.observability.
    trace_id_middleware` (Sprint 1) already attached to the request
    (`request.state.trace_id`, echoed via the `X-Trace-Id` header), so
    a span always correlates back to the log lines
    `platform.observability.correlation_middleware` (Sprint 10) bound
    into structlog for that same request — one correlation id shared
    by logs, traces and metrics, never a second id scheme."""

    id: str
    trace_id: str
    kind: SpanKind
    name: str
    parent_span_id: str | None = None
    firm_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    status: SpanStatus = SpanStatus.OK
    attributes: dict[str, str] = field(default_factory=dict)

    def duration_ms(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds() * 1000
