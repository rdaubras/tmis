from dataclasses import dataclass
from enum import StrEnum


class GraphOrigin(StrEnum):
    """Which of the three existing graphs a `FederatedNodeRef` came
    from — the vocabulary `entity_resolution` reuses to tag where each
    occurrence of a resolved entity was found, rather than inventing a
    second "which graph" enum."""

    CASE_GRAPH = "case_graph"
    DOCUMENT_KNOWLEDGE_GRAPH = "document_knowledge_graph"
    CABINET_ONTOLOGY = "cabinet_ontology"


@dataclass(frozen=True, slots=True)
class FederatedNodeRef:
    """A node as seen through federation — always a thin projection of
    a node/object owned by one of the three existing graphs, never a
    copy stored anywhere. `node_type` is that graph's own type value
    (`CaseNodeType`, `NodeType`, or a cabinet `RelationType` when the
    neighbor comes from `OntologyEngine`, which does not type its
    objects itself)."""

    origin: GraphOrigin
    node_id: str
    label: str
    node_type: str


@dataclass(frozen=True, slots=True)
class FederatedNeighborhood:
    """One scope's worth of "what is connected to this id" — the unit
    `cross_scope_neighborhood` collects one-per-occurrence to answer a
    query that spans dossier, document, and cabinet scope at once."""

    subject: FederatedNodeRef
    neighbors: tuple[FederatedNodeRef, ...]
