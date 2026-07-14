import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class GraphNodeType(StrEnum):
    """The node types the Sprint 25 prompt asks for. Each node is a
    pointer into whatever bounded context already owns that entity —
    never a copy of its content (see `GraphNode.ref_id`)."""

    CONCEPT = "concept"
    LAW_ARTICLE = "law_article"
    JURISPRUDENCE = "jurisprudence"
    DECISION = "decision"
    CONTRACT = "contract"
    CLAUSE = "clause"
    PARTY = "party"
    LEGAL_ENTITY = "legal_entity"
    CASE = "case"
    ARGUMENT = "argument"
    RISK = "risk"
    PROCEDURE = "procedure"
    DOCUMENT = "document"


def new_graph_node_id() -> str:
    return f"node-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class GraphNode:
    """A pointer, not a payload: `ref_id` is the id of the real entity
    in its owning context (a `KnowledgeObject` id for CLAUSE/
    JURISPRUDENCE/DECISION, a `case_intelligence.cases.Case` id for
    CASE, a `case_intelligence.actors.Actor` id for PARTY/
    LEGAL_ENTITY, a `legal_reasoning` argument id for ARGUMENT, a
    document id for DOCUMENT). Resolving `ref_id` back into real
    content is always the caller's job, through that context's own
    port — the graph never fetches it."""

    id: str
    firm_id: str
    node_type: GraphNodeType
    ref_id: str
    label: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
