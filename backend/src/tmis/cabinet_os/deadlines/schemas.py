from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DeadlineStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    MISSED = "missed"


@dataclass(slots=True)
class Deadline:
    """A deadline, computed automatically from a registered event or
    created manually (see docs/39-cabinet-os.md — Deadline Engine).
    `alert_offsets` are configurable durations *before* `due_at` at
    which an alert should fire — the engine itself does not send
    alerts, it only computes the schedule (see `list_due_alerts`)."""

    id: str
    firm_id: str
    case_id: str
    label: str
    due_at: datetime
    status: DeadlineStatus = DeadlineStatus.PENDING
    source_event_label: str = ""
    alert_offsets: list[timedelta] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DeadlineCandidate:
    """One deadline a `DeadlineRulePort` proposes from a trigger event
    — not yet persisted, not yet assigned an id or a firm."""

    label: str
    due_at: datetime
    alert_offsets: list[timedelta] = field(default_factory=list)
