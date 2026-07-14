from collections.abc import Sequence

from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.case_intelligence.relationships.ports import CaseGraphPort
from tmis.document_intelligence.knowledge.ports import KnowledgeGraphPort
from tmis.knowledge_graph.federation.schemas import (
    FederatedNeighborhood,
    FederatedNodeRef,
    GraphOrigin,
)


class FederationQueryEngine:
    """Answers cross-scope queries by composing the three existing
    graph ports/engines — never a fourth graph, never its own storage.

    Each `*_neighborhood` method is a thin projection of one existing
    port's `get_node`/`get_neighbors` (or `OntologyEngine.relations_for`)
    call. `cross_scope_neighborhood` is the entry point for "tout ce qui
    touche l'entité X, dans quel dossier, quel document, quelle
    recommandation cabinet" — it takes the occurrences already
    identified as the same entity (typically an `entity_resolution.
    ResolvedEntity`'s occurrences) and gathers one `FederatedNeighborhood`
    per scope where that entity was found.
    """

    def __init__(
        self,
        case_graph: CaseGraphPort,
        knowledge_graph: KnowledgeGraphPort,
        ontology_engine: OntologyEngine,
    ) -> None:
        self._case_graph = case_graph
        self._knowledge_graph = knowledge_graph
        self._ontology_engine = ontology_engine

    def case_neighborhood(self, node_id: str) -> FederatedNeighborhood | None:
        node = self._case_graph.get_node(node_id)
        if node is None:
            return None
        neighbors = tuple(
            FederatedNodeRef(
                origin=GraphOrigin.CASE_GRAPH, node_id=n.id, label=n.label, node_type=n.type.value
            )
            for n in self._case_graph.get_neighbors(node_id)
        )
        subject = FederatedNodeRef(
            origin=GraphOrigin.CASE_GRAPH,
            node_id=node.id,
            label=node.label,
            node_type=node.type.value,
        )
        return FederatedNeighborhood(subject=subject, neighbors=neighbors)

    def document_neighborhood(self, node_id: str) -> FederatedNeighborhood | None:
        node = self._knowledge_graph.get_node(node_id)
        if node is None:
            return None
        neighbors = tuple(
            FederatedNodeRef(
                origin=GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH,
                node_id=n.id,
                label=n.label,
                node_type=n.type.value,
            )
            for n in self._knowledge_graph.get_neighbors(node_id)
        )
        subject = FederatedNodeRef(
            origin=GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH,
            node_id=node.id,
            label=node.label,
            node_type=node.type.value,
        )
        return FederatedNeighborhood(subject=subject, neighbors=neighbors)

    def cabinet_neighborhood(self, firm_id: str, object_id: str) -> FederatedNeighborhood:
        relations = self._ontology_engine.relations_for(firm_id, object_id)
        neighbor_refs: list[FederatedNodeRef] = []
        for relation in relations:
            other_id = (
                relation.target_id if relation.source_id == object_id else relation.source_id
            )
            neighbor_refs.append(
                FederatedNodeRef(
                    origin=GraphOrigin.CABINET_ONTOLOGY,
                    node_id=other_id,
                    label=other_id,
                    node_type=relation.relation_type.value,
                )
            )
        neighbors = tuple(neighbor_refs)
        subject = FederatedNodeRef(
            origin=GraphOrigin.CABINET_ONTOLOGY,
            node_id=object_id,
            label=object_id,
            node_type="knowledge_object",
        )
        return FederatedNeighborhood(subject=subject, neighbors=neighbors)

    def cross_scope_neighborhood(
        self, firm_id: str, occurrences: Sequence[tuple[GraphOrigin, str]]
    ) -> tuple[FederatedNeighborhood, ...]:
        results: list[FederatedNeighborhood] = []
        for origin, node_id in occurrences:
            neighborhood: FederatedNeighborhood | None
            if origin is GraphOrigin.CASE_GRAPH:
                neighborhood = self.case_neighborhood(node_id)
            elif origin is GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH:
                neighborhood = self.document_neighborhood(node_id)
            else:
                neighborhood = self.cabinet_neighborhood(firm_id, node_id)
            if neighborhood is not None:
                results.append(neighborhood)
        return tuple(results)
