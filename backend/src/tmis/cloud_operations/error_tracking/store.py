from tmis.cloud_operations.error_tracking.schemas import ErrorEvent


class InMemoryErrorEventStore:
    def __init__(self) -> None:
        self._events: list[ErrorEvent] = []

    def save(self, event: ErrorEvent) -> None:
        self._events.append(event)

    def list_recent(self, limit: int) -> list[ErrorEvent]:
        return list(reversed(self._events))[:limit]

    def list_for_source(self, source: str) -> list[ErrorEvent]:
        return [e for e in self._events if e.source == source]
