from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.document_intelligence.schemas.timeline import TimelineEvent


class FactEnginePort(Protocol):
    """Port implemented by every interchangeable fact-aggregation engine."""

    def ingest(
        self, facts: list[Fact], events: list[TimelineEvent], document_id: str
    ) -> list[Fact]: ...
