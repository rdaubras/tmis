from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.timeline.schemas import TimelineInconsistency
from tmis.legal_reasoning.conflicts.schemas import Conflict


class ConflictDetectorPort(Protocol):
    """Port implemented by every interchangeable conflict detector."""

    def detect(
        self, facts: list[Fact], timeline_inconsistencies: list[TimelineInconsistency]
    ) -> list[Conflict]: ...
