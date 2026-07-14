import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cabinet_knowledge.feedback.schemas import FeedbackAction

__all__ = ["FeedbackAction", "GraphFeedback", "new_graph_feedback_id"]


def new_graph_feedback_id() -> str:
    return f"gfb-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class GraphFeedback:
    """Reuses `cabinet_knowledge.feedback.FeedbackAction` (ACCEPT/
    MODIFY/REJECT/ANNOTATE/EXPLAIN) directly — the Sprint 25 Human
    Validation Loop needs the same five actions, applied to subjects
    `cabinet_knowledge.feedback.FeedbackEngine` cannot cover because
    they are not `KnowledgeObject`s: a `GraphNode`, a
    `KnowledgeRelation`, or an `entity_resolution.ResolutionMatch`."""

    id: str
    firm_id: str
    subject_id: str
    action: FeedbackAction
    author: str
    comment: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
