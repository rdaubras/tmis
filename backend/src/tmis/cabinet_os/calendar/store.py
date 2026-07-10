from datetime import datetime

from tmis.cabinet_os.calendar.schemas import CalendarEvent


class InMemoryCalendarStore:
    """Implements `CalendarStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._events: dict[str, CalendarEvent] = {}

    def get(self, event_id: str) -> CalendarEvent | None:
        return self._events.get(event_id)

    def save(self, event: CalendarEvent) -> None:
        self._events[event.id] = event

    def delete(self, event_id: str) -> None:
        self._events.pop(event_id, None)

    def list_for_range(
        self, firm_id: str, starts_at: datetime, ends_at: datetime
    ) -> list[CalendarEvent]:
        return [
            e
            for e in self._events.values()
            if e.firm_id == firm_id and starts_at <= e.starts_at < ends_at
        ]

    def list_for_firm(self, firm_id: str) -> list[CalendarEvent]:
        return [e for e in self._events.values() if e.firm_id == firm_id]
