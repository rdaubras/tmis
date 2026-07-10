import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar, cast


@dataclass(frozen=True, kw_only=True)
class CollaborationEvent:
    """Base class for every event published by the Legal Collaboration
    Engine. Deliberately its own hierarchy, separate from
    `tmis.ai.events.events.Event`: the LCE must work without importing
    anything from `tmis.ai` (see docs/33-legal-collaboration.md), so it
    cannot share the Kernel's event base class even though the shape is
    the same. Any AI-facing module that wants collaboration events
    subscribes to `CollaborationEventBus` directly.
    """

    workspace_id: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


EventT = TypeVar("EventT", bound=CollaborationEvent)
EventHandler = Callable[[CollaborationEvent], Awaitable[None]]


class CollaborationEventBus:
    """In-memory publish/subscribe bus for collaboration events —
    mirrors `tmis.ai.events.bus.EventBus`'s shape but is a fully
    standalone implementation with zero import from `tmis.ai`."""

    def __init__(self) -> None:
        self._subscribers: dict[type[CollaborationEvent], list[EventHandler]] = defaultdict(list)
        self._history: list[CollaborationEvent] = []

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].append(cast(EventHandler, handler))

    def unsubscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].remove(cast(EventHandler, handler))

    async def publish(self, event: CollaborationEvent) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)

    @property
    def history(self) -> list[CollaborationEvent]:
        return list(self._history)
