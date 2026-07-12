from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from tmis.identity_platform.security_events.schemas import SecurityEvent

EventT = TypeVar("EventT", bound=SecurityEvent)
EventHandler = Callable[[SecurityEvent], Awaitable[None]]


class SecurityEventBus:
    """In-memory publish/subscribe bus for identity-platform security
    events — same standalone shape as `WorkflowEventBus`/
    `IntegrationEventBus`. Unlike those, also supports
    `subscribe_all()` — a handler that receives every event
    regardless of type, which `audit.SecurityAuditEngine` uses to
    build a complete, append-only trail without subscribing to each
    event class individually."""

    def __init__(self) -> None:
        self._subscribers: dict[type[SecurityEvent], list[EventHandler]] = defaultdict(list)
        self._global_subscribers: list[EventHandler] = []
        self._history: list[SecurityEvent] = []

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].append(cast(EventHandler, handler))

    def subscribe_all(self, handler: EventHandler) -> None:
        self._global_subscribers.append(handler)

    async def publish(self, event: SecurityEvent) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)
        for handler in self._global_subscribers:
            await handler(event)

    @property
    def history(self) -> list[SecurityEvent]:
        return list(self._history)
