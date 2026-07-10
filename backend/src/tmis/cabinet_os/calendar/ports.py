from datetime import datetime
from typing import Protocol

from tmis.cabinet_os.calendar.schemas import CalendarEvent, CalendarEventType, CalendarView


class CalendarStorePort(Protocol):
    def get(self, event_id: str) -> CalendarEvent | None: ...

    def save(self, event: CalendarEvent) -> None: ...

    def delete(self, event_id: str) -> None: ...

    def list_for_range(
        self, firm_id: str, starts_at: datetime, ends_at: datetime
    ) -> list[CalendarEvent]: ...

    def list_for_firm(self, firm_id: str) -> list[CalendarEvent]: ...


class CalendarEnginePort(Protocol):
    """Port implemented by every interchangeable calendar engine."""

    def schedule(
        self,
        firm_id: str,
        event_type: CalendarEventType,
        title: str,
        starts_at: datetime,
        *,
        ends_at: datetime | None = None,
        case_id: str | None = None,
        participant_ids: set[str] | None = None,
        location: str = "",
        related_id: str | None = None,
    ) -> CalendarEvent: ...

    def reschedule(
        self, event_id: str, starts_at: datetime, ends_at: datetime | None = None
    ) -> CalendarEvent: ...

    def cancel(self, event_id: str) -> None: ...

    def view(
        self, firm_id: str, view: CalendarView, reference_date: datetime
    ) -> list[CalendarEvent]: ...
