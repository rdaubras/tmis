from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Hearing:
    """A court hearing (see docs/39-cabinet-os.md — Hearing Engine):
    jurisdiction, chamber, room, participants, preparatory documents
    and, once held, the decision. `calendar_event_id`/
    `reminder_event_id` link to the `CalendarEvent`s the Hearing Engine
    creates automatically — the calendar is the single source of truth
    for *when*, the hearing for *what*."""

    id: str
    firm_id: str
    case_id: str
    jurisdiction: str
    chamber: str
    scheduled_at: datetime
    room: str = ""
    participant_ids: set[str] = field(default_factory=set)
    preparatory_document_ids: set[str] = field(default_factory=set)
    decision: str | None = None
    decided_at: datetime | None = None
    calendar_event_id: str | None = None
    reminder_event_id: str | None = None
    created_at: datetime | None = None
