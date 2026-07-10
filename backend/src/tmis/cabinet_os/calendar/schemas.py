from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CalendarEventType(str, Enum):
    HEARING = "hearing"
    APPOINTMENT = "appointment"
    CALL = "call"
    DEADLINE = "deadline"
    REMINDER = "reminder"


class CalendarView(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    AGENDA = "agenda"


@dataclass(slots=True)
class CalendarEvent:
    """One entry in the firm's business calendar (see
    docs/41-guide-calendrier.md): a hearing, an appointment, a call, a
    deadline or a reminder. `related_id` optionally points to the
    aggregate that produced this event (a `Hearing` or `Deadline` id) —
    the calendar never embeds that aggregate, only its id."""

    id: str
    firm_id: str
    event_type: CalendarEventType
    title: str
    starts_at: datetime
    ends_at: datetime | None = None
    case_id: str | None = None
    participant_ids: set[str] = field(default_factory=set)
    location: str = ""
    related_id: str | None = None
    created_at: datetime | None = None
