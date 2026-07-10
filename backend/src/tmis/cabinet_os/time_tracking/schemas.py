from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    RESEARCH = "research"
    DRAFTING = "drafting"
    HEARING_PREP = "hearing_prep"
    CLIENT_MEETING = "client_meeting"
    CALL = "call"
    ADMINISTRATIVE = "administrative"
    COURT_APPEARANCE = "court_appearance"
    OTHER = "other"


class EntryMethod(str, Enum):
    """The "plusieurs méthodes de saisie" required by the brief: typed
    in after the fact, timed live, or a one-tap preset duration."""

    MANUAL = "manual"
    TIMER = "timer"
    QUICK_ENTRY = "quick_entry"


@dataclass(slots=True)
class TimeEntry:
    """One unit of tracked time (see docs/39-cabinet-os.md — Time
    Tracking Engine). `duration_minutes`/`ended_at` are `None` while a
    `TIMER`-method entry is still running; `TimeTrackingEngine.
    stop_timer` fills them in."""

    id: str
    firm_id: str
    collaborator_id: str
    case_id: str
    activity_type: ActivityType
    entry_method: EntryMethod
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    task_id: str | None = None
    comments: str = ""
    billable: bool = True
    created_at: datetime | None = None
