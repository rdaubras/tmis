import re

from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.timeline import TimelineEvent

_MONTH_NUMBERS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "décembre": 12,
}
_FRENCH_DATE_RE = re.compile(r"(\d{1,2})\s+(\w+)\s+(\d{4})", re.IGNORECASE)
_NUMERIC_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2,4})")
_CONTEXT_RADIUS = 60


def _sort_key(date_value: str) -> tuple[int, int, int]:
    match = _FRENCH_DATE_RE.match(date_value)
    if match:
        day, month_name, year = match.groups()
        month = _MONTH_NUMBERS.get(month_name.lower(), 0)
        return (int(year), month, int(day))
    match = _NUMERIC_DATE_RE.match(date_value)
    if match:
        day, month_str, year = match.groups()
        year_int = int(year) + 2000 if len(year) == 2 else int(year)
        return (year_int, int(month_str), int(day))
    return (0, 0, 0)


class ChronologicalTimelineBuilder:
    """Implements `TimelineBuilderPort`: extracts a short context snippet
    around each `EntityType.DATE` entity and sorts the resulting events
    chronologically (best-effort — dates the parser cannot recognize sort
    first, at key (0, 0, 0))."""

    def build(
        self, document_id: str, text: str, entities: list[ExtractedEntity]
    ) -> list[TimelineEvent]:
        events = [
            TimelineEvent(
                date=entity.value,
                description=self._context_snippet(text, entity),
                document_id=document_id,
                confidence=entity.confidence,
            )
            for entity in entities
            if entity.type == EntityType.DATE
        ]
        return sorted(events, key=lambda event: _sort_key(event.date))

    def _context_snippet(self, text: str, entity: ExtractedEntity) -> str:
        if entity.span_start is None or entity.span_end is None:
            return entity.value
        start = max(0, entity.span_start - _CONTEXT_RADIUS)
        end = min(len(text), entity.span_end + _CONTEXT_RADIUS)
        snippet = text[start:end].replace("\n", " ")
        return re.sub(r"\s+", " ", snippet).strip()
