import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_semantic_link_id() -> str:
    return f"semlink-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class SemanticLink:
    """A similarity relation between two knowledge-graph objects
    (from any of the three existing graphs), scored by cosine
    similarity of their embeddings. Explicitly not a `CaseEdge`/
    `KnowledgeEdge`/`KnowledgeRelation` — those mean "connected to";
    this means "reads as similar to", and the two can both exist
    between the same pair of ids without conflict."""

    id: str
    source_id: str
    target_id: str
    score: float
    embedding_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
