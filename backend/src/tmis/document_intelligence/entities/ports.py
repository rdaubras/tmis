from typing import Protocol

from tmis.document_intelligence.schemas.entities import ExtractedEntity


class EntityExtractorPort(Protocol):
    """Port implemented by every interchangeable entity extraction engine."""

    def extract(self, text: str) -> list[ExtractedEntity]: ...
