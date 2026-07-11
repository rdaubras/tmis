from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from tmis.workflow_automation.event_bus.schemas import WorkflowEvent

EventT = TypeVar("EventT", bound=WorkflowEvent)
EventHandler = Callable[[WorkflowEvent], Awaitable[None]]


class WorkflowEventBus:
    """In-memory publish/subscribe bus for workflow-automation events —
    same shape as `CollaborationEventBus`/`GovernanceEventBus`, fully
    standalone."""

    def __init__(self) -> None:
        self._subscribers: dict[type[WorkflowEvent], list[EventHandler]] = defaultdict(list)
        self._history: list[WorkflowEvent] = []

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].append(cast(EventHandler, handler))

    def unsubscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._subscribers[event_type].remove(cast(EventHandler, handler))

    async def publish(self, event: WorkflowEvent) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)

    @property
    def history(self) -> list[WorkflowEvent]:
        return list(self._history)
