from typing import Protocol

from tmis.document_intelligence.schemas.entities import ExtractedEntity
from tmis.document_intelligence.schemas.timeline import TimelineEvent


class TimelineBuilderPort(Protocol):
    def build(
        self, document_id: str, text: str, entities: list[ExtractedEntity]
    ) -> list[TimelineEvent]: ...
