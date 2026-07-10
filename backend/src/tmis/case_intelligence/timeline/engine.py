import re
from collections import defaultdict

from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency
from tmis.document_intelligence.schemas.timeline import TimelineEvent

_WHITESPACE_RE = re.compile(r"\s+")
_MONTH_NUMBERS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "décembre": 12,
}
_FRENCH_DATE_RE = re.compile(r"(\d{1,2})\s+(\w+)\s+(\d{4})", re.IGNORECASE)
_NUMERIC_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")
_CONFIRMATION_BOOST = 0.1


def _normalize(description: str) -> str:
    return _WHITESPACE_RE.sub(" ", description.strip().lower())


def _sort_key(date_value: str) -> tuple[int, int, int]:
    match = _FRENCH_DATE_RE.match(date_value)
    if match:
        day, month_name, year = match.groups()
        return (int(year), _MONTH_NUMBERS.get(month_name.lower(), 0), int(day))
    match = _NUMERIC_DATE_RE.match(date_value)
    if match:
        day, month_str, year = match.groups()
        year_int = int(year) + 2000 if len(year) == 2 else int(year)
        return (year_int, int(month_str), int(day))
    return (0, 0, 0)


class CaseTimelineEngine:
    """Implements `TimelineConsolidatorPort`: merges per-document timeline
    events into the case's consolidated chronology, corroborating an
    entry already on record instead of duplicating it, and flags any
    date carrying more than one distinct description as a temporal
    inconsistency (see docs/19-case-intelligence.md).
    """

    def consolidate(
        self, entries: list[CaseTimelineEntry], events: list[TimelineEvent]
    ) -> list[CaseTimelineEntry]:
        updated = list(entries)

        for event in events:
            normalized = _normalize(event.description)
            match_index = next(
                (
                    i
                    for i, entry in enumerate(updated)
                    if entry.date == event.date and _normalize(entry.description) == normalized
                ),
                None,
            )
            if match_index is not None:
                existing = updated[match_index]
                if event.document_id in existing.document_ids:
                    continue
                updated[match_index] = CaseTimelineEntry(
                    date=existing.date,
                    description=existing.description,
                    document_ids=(*existing.document_ids, event.document_id),
                    confidence=min(1.0, existing.confidence + _CONFIRMATION_BOOST),
                )
                continue
            updated.append(
                CaseTimelineEntry(
                    date=event.date,
                    description=event.description,
                    document_ids=(event.document_id,),
                    confidence=event.confidence,
                )
            )

        return sorted(updated, key=lambda entry: _sort_key(entry.date))

    def detect_inconsistencies(
        self, entries: list[CaseTimelineEntry]
    ) -> list[TimelineInconsistency]:
        by_date: dict[str, list[CaseTimelineEntry]] = defaultdict(list)
        for entry in entries:
            by_date[entry.date].append(entry)
        return [
            TimelineInconsistency(date=date, entries=tuple(group))
            for date, group in by_date.items()
            if len(group) > 1
        ]
