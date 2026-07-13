import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_telemetry_event_id() -> str:
    return f"tev-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """A generic, historized cross-cutting observability event —
    distinct in scope from the many domain event buses already in
    TMIS (`WorkflowEventBus`, `IntegrationEventBus`, `SecurityEventBus`,
    ...): those carry *business* events a module reacts to; this one
    is a fire-and-forget observability signal ("cache evicted",
    "circuit opened", "chaos experiment started") nothing downstream
    is required to react to, only to observe."""

    id: str
    name: str
    firm_id: str | None
    payload: dict[str, str] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
