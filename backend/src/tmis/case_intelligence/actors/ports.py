from typing import Protocol

from tmis.case_intelligence.actors.schemas import Actor
from tmis.document_intelligence.schemas.entities import ExtractedEntity


class ActorMergerPort(Protocol):
    """Port implemented by every interchangeable actor-resolution engine."""

    def merge(
        self, actors: list[Actor], entities: list[ExtractedEntity], document_id: str
    ) -> list[Actor]: ...
