from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tmis.ai.events.events import Event

EventT = TypeVar("EventT", bound=Event)
EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """In-memory publish/subscribe bus.

    Every component in the AI Kernel communicates through events rather
    than direct method calls, so a new subscriber (e.g. an audit logger, a
    future notification service) can be added without touching publishers.
    """

    def __init__(self) -> None:
        self._subscribers: dict[type[Event], list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []

    def subscribe(self, event_type: type[EventT], handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type[EventT], handler: EventHandler) -> None:
        self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            await handler(event)

    @property
    def history(self) -> list[Event]:
        return list(self._history)
