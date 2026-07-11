from dataclasses import dataclass
from enum import StrEnum


class TimelineEntryKind(StrEnum):
    FACT = "fact"
    EVENT = "event"
    DEADLINE = "deadline"
    PROPOSED_ACTION = "proposed_action"


@dataclass(frozen=True, slots=True)
class StrategicTimelineEntry:
    """One point in a case's strategic chronology. Inspired by, but
    not reused from, `case_intelligence.timeline.CaseTimelineEntry` —
    this timeline additionally merges in proposed actions from
    `action_planner`, which the case-intelligence timeline has no
    notion of."""

    date: str
    kind: TimelineEntryKind
    description: str
    reference: str
