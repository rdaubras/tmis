import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RelationType(StrEnum):
    CITES = "cites"
    SUPERSEDES = "supersedes"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    CONTRADICTS = "contradicts"
    APPLIES_TO = "applies_to"


def new_relation_id() -> str:
    return f"rel-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class KnowledgeRelation:
    id: str
    firm_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
