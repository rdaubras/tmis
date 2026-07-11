from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from tmis.platform_sdk.events_sdk.schemas import PlatformEvent

EventHandler = Callable[[PlatformEvent], Awaitable[None]]


class PlatformEventBus:
    """Satisfies `tmis.platform_sdk.sdk.ports.EventPublisherPort`
    directly — the sprint's "EVENT SDK": a plugin subscribes to a
    named event and is invoked with the full `PlatformEvent` whenever
    any part of TMIS (or another plugin) publishes it."""

    def __init__(self, source_context: str = "platform_sdk") -> None:
        self._source_context = source_context
        self._handlers: defaultdict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[PlatformEvent] = []

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        handlers = self._handlers[event_name]
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        event = PlatformEvent(
            event_name=event_name, source_context=self._source_context, payload=payload
        )
        self._history.append(event)
        for handler in self._handlers[event_name]:
            await handler(event)

    @property
    def history(self) -> list[PlatformEvent]:
        return list(self._history)
