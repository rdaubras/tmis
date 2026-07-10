from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CaseTimelineEntry:
    """One dated entry in the case's consolidated chronology. Multiple
    documents can corroborate the same entry — `document_ids` lists all
    of them."""

    date: str
    description: str
    document_ids: tuple[str, ...]
    confidence: float


@dataclass(frozen=True, slots=True)
class TimelineInconsistency:
    """Flags that two or more entries disagree about the same date."""

    date: str
    entries: tuple[CaseTimelineEntry, ...]
    reason: str = field(default="Plusieurs descriptions différentes pour la même date.")
