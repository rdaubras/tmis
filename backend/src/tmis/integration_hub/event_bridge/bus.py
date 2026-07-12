from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from tmis.integration_hub.event_bridge.schemas import IntegrationEvent

EventT = TypeVar("EventT", bound=IntegrationEvent)
EventHandler = Callable[[IntegrationEvent], Awaitable[None]]


class IntegrationEventBus:
    """In-memory publish/subscribe bus for integration-hub events —
    same shape as `WorkflowEventBus`/`CollaborationEventBus`, fully
    standalone."""

    def __init__(self) -> None:
        self._subscribers: dict[type[IntegrationEvent], list[EventHandler]] = defaultdict(list)
        self._history: list[IntegrationEvent] = []

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].append(cast(EventHandler, handler))

    def unsubscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].remove(cast(EventHandler, handler))

    async def publish(self, event: IntegrationEvent) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)

    @property
    def history(self) -> list[IntegrationEvent]:
        return list(self._history)
