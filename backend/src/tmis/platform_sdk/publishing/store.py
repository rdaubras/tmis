from tmis.platform_sdk.publishing.schemas import PublishingEvent


class InMemoryPublishingStore:
    def __init__(self) -> None:
        self._events: list[PublishingEvent] = []

    def append(self, event: PublishingEvent) -> None:
        self._events.append(event)

    def history(self, plugin_id: str) -> list[PublishingEvent]:
        return [e for e in self._events if e.plugin_id == plugin_id]
