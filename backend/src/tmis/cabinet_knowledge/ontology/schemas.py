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
    # Added in Sprint 25 (Legal Knowledge Graph) — the graph's own
    # relation types, on the same enum rather than a second
    # vocabulary: an article/clause/argument is still just a node,
    # a `KnowledgeRelation` between two nodes either resolves to a
    # `KnowledgeObject` id (existing types) or to a cross-context
    # pointer (these three).
    INFLUENCES = "influences"
    APPEARS_IN = "appears_in"
    MENTIONS = "mentions"
    SAME_AS = "same_as"


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
    # explanation/confidence added in Sprint 25 — "chaque relation doit
    # être explicable" — optional and defaulted so every Sprint 12
    # caller keeps working unchanged.
    explanation: str | None = None
    confidence: float = 1.0
