from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNode


class InMemoryGraphNodeStore:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}

    def save(self, node: GraphNode) -> None:
        self._nodes[node.id] = node

    def get(self, firm_id: str, node_id: str) -> GraphNode | None:
        node = self._nodes.get(node_id)
        if node is None or node.firm_id != firm_id:
            return None
        return node

    def list_for_firm(self, firm_id: str) -> list[GraphNode]:
        return [node for node in self._nodes.values() if node.firm_id == firm_id]


class InMemoryGraphRelationStore:
    def __init__(self) -> None:
        self._relations: dict[str, KnowledgeRelation] = {}

    def add(self, relation: KnowledgeRelation) -> None:
        self._relations[relation.id] = relation

    def list_for_node(self, firm_id: str, node_id: str) -> list[KnowledgeRelation]:
        return [
            r
            for r in self._relations.values()
            if r.firm_id == firm_id and (r.source_id == node_id or r.target_id == node_id)
        ]

    def get(self, firm_id: str, relation_id: str) -> KnowledgeRelation | None:
        relation = self._relations.get(relation_id)
        if relation is None or relation.firm_id != firm_id:
            return None
        return relation
