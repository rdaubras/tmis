import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar, cast


@dataclass(frozen=True, kw_only=True)
class GovernanceEvent:
    """Base class for every event published by the AI Governance &
    Explainability Platform. Its own hierarchy, separate from
    `tmis.ai.events.events.Event`: `tmis.ai_governance` observes
    productions from every bounded context (legal_reasoning,
    legal_drafting, ai_team, ai_fabric...) and must not force a
    dependency in the other direction — mirrors
    `tmis.collaboration.event_bus.CollaborationEvent`'s isolation
    rationale (see docs/33-legal-collaboration.md)."""

    firm_id: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class ExplanationGenerated(GovernanceEvent):
    production_id: str
    explanation_id: str


@dataclass(frozen=True, kw_only=True)
class RiskDetected(GovernanceEvent):
    production_id: str
    risk_id: str
    severity: str


@dataclass(frozen=True, kw_only=True)
class PolicyEvaluated(GovernanceEvent):
    production_id: str
    allowed: bool


@dataclass(frozen=True, kw_only=True)
class ValidationRecorded(GovernanceEvent):
    validation_id: str
    decision: str


@dataclass(frozen=True, kw_only=True)
class DecisionRecorded(GovernanceEvent):
    decision_record_id: str


@dataclass(frozen=True, kw_only=True)
class GovernanceRunCompleted(GovernanceEvent):
    production_id: str
    duration_ms: float


EventT = TypeVar("EventT", bound=GovernanceEvent)
EventHandler = Callable[[GovernanceEvent], Awaitable[None]]


class GovernanceEventBus:
    """In-memory publish/subscribe bus for AI Governance events —
    mirrors `tmis.ai.events.bus.EventBus`'s shape but is a fully
    standalone implementation, consistent with `GovernanceEvent`'s
    isolation from `tmis.ai.events`."""

    def __init__(self) -> None:
        self._subscribers: dict[type[GovernanceEvent], list[EventHandler]] = defaultdict(list)
        self._history: list[GovernanceEvent] = []

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].append(cast(EventHandler, handler))

    def unsubscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].remove(cast(EventHandler, handler))

    async def publish(self, event: GovernanceEvent) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)

    @property
    def history(self) -> list[GovernanceEvent]:
        return list(self._history)
