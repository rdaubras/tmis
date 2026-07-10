from typing import Protocol

from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency
from tmis.document_intelligence.schemas.timeline import TimelineEvent


class TimelineConsolidatorPort(Protocol):
    """Port implemented by every interchangeable case-timeline engine."""

    def consolidate(
        self, entries: list[CaseTimelineEntry], events: list[TimelineEvent]
    ) -> list[CaseTimelineEntry]: ...

    def detect_inconsistencies(
        self, entries: list[CaseTimelineEntry]
    ) -> list[TimelineInconsistency]: ...
