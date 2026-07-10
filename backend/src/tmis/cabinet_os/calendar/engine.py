import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.calendar.ports import CalendarStorePort
from tmis.cabinet_os.calendar.schemas import CalendarEvent, CalendarEventType, CalendarView


class ConfigurableCalendarEngine:
    """Implements `CalendarEnginePort` (see docs/41-guide-calendrier.md):
    hearings, appointments, calls, deadlines and reminders in one
    business calendar, with day/week/month/agenda views computed on
    read — no separate storage per view."""

    def __init__(self, store: CalendarStorePort) -> None:
        self._store = store

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
    ) -> CalendarEvent:
        event = CalendarEvent(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            event_type=event_type,
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            case_id=case_id,
            participant_ids=set(participant_ids or set()),
            location=location,
            related_id=related_id,
            created_at=datetime.now(UTC),
        )
        self._store.save(event)
        return event

    def reschedule(
        self, event_id: str, starts_at: datetime, ends_at: datetime | None = None
    ) -> CalendarEvent:
        event = self._store.get(event_id)
        if event is None:
            raise ValueError(f"Unknown calendar event {event_id!r}")
        event.starts_at = starts_at
        event.ends_at = ends_at
        self._store.save(event)
        return event

    def cancel(self, event_id: str) -> None:
        if self._store.get(event_id) is None:
            raise ValueError(f"Unknown calendar event {event_id!r}")
        self._store.delete(event_id)

    def view(
        self, firm_id: str, view: CalendarView, reference_date: datetime
    ) -> list[CalendarEvent]:
        if view is CalendarView.AGENDA:
            upcoming = [
                e for e in self._store.list_for_firm(firm_id) if e.starts_at >= reference_date
            ]
            return sorted(upcoming, key=lambda e: e.starts_at)
        start, end = self._window(view, reference_date)
        events = self._store.list_for_range(firm_id, start, end)
        return sorted(events, key=lambda e: e.starts_at)

    def _window(self, view: CalendarView, reference_date: datetime) -> tuple[datetime, datetime]:
        day_start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        if view is CalendarView.DAY:
            return day_start, day_start + timedelta(days=1)
        if view is CalendarView.WEEK:
            week_start = day_start - timedelta(days=day_start.weekday())
            return week_start, week_start + timedelta(days=7)
        if view is CalendarView.MONTH:
            month_start = day_start.replace(day=1)
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month + 1)
            return month_start, next_month
        raise ValueError(f"Unsupported view: {view}")
