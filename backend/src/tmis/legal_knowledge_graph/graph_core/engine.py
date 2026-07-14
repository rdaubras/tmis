from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation, RelationType, new_relation_id
from tmis.legal_knowledge_graph.graph_core.ports import GraphNodeStorePort, GraphRelationStorePort
from tmis.legal_knowledge_graph.graph_core.schemas import (
    GraphNode,
    GraphNodeType,
    new_graph_node_id,
)

_RELATION_VERBS: dict[RelationType, str] = {
    RelationType.CITES: "cite",
    RelationType.SUPERSEDES: "remplace",
    RelationType.DERIVED_FROM: "dérive de",
    RelationType.RELATED_TO: "est lié à",
    RelationType.CONTRADICTS: "contredit",
    RelationType.APPLIES_TO: "s'applique à",
    RelationType.INFLUENCES: "influence",
    RelationType.APPEARS_IN: "apparaît dans",
    RelationType.MENTIONS: "mentionne",
    RelationType.SAME_AS: "désigne la même entité que",
}


class GraphEngine:
    """The Legal Knowledge Graph's single entry point: nodes are
    pointers into whatever context owns the real entity, relations
    reuse `cabinet_knowledge.ontology`'s `KnowledgeRelation`/
    `RelationType` vocabulary directly rather than inventing a second
    one — only the storage is graph-scoped (nodes here are not always
    `KnowledgeObject`s, so `ontology.OntologyEngine`'s own store,
    which requires exactly that, cannot be reused for storage)."""

    def __init__(self, nodes: GraphNodeStorePort, relations: GraphRelationStorePort) -> None:
        self._nodes = nodes
        self._relations = relations

    def add_node(
        self, firm_id: str, node_type: GraphNodeType, ref_id: str, label: str
    ) -> GraphNode:
        node = GraphNode(
            id=new_graph_node_id(), firm_id=firm_id, node_type=node_type, ref_id=ref_id, label=label
        )
        self._nodes.save(node)
        return node

    def get_node(self, firm_id: str, node_id: str) -> GraphNode:
        node = self._nodes.get(firm_id, node_id)
        if node is None:
            raise KeyError(node_id)
        return node

    def list_nodes(self, firm_id: str, node_type: GraphNodeType | None = None) -> list[GraphNode]:
        nodes = self._nodes.list_for_firm(firm_id)
        if node_type is not None:
            nodes = [n for n in nodes if n.node_type is node_type]
        return nodes

    def link(
        self,
        firm_id: str,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        *,
        explanation: str | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeRelation:
        source = self.get_node(firm_id, source_id)
        target = self.get_node(firm_id, target_id)
        relation = KnowledgeRelation(
            id=new_relation_id(),
            firm_id=firm_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            explanation=explanation or self._default_explanation(source, target, relation_type),
            confidence=confidence,
        )
        self._relations.add(relation)
        return relation

    def relations_for(self, firm_id: str, node_id: str) -> list[KnowledgeRelation]:
        return self._relations.list_for_node(firm_id, node_id)

    def neighbors(self, firm_id: str, node_id: str) -> list[GraphNode]:
        neighbor_ids = set()
        for relation in self.relations_for(firm_id, node_id):
            neighbor_ids.add(
                relation.target_id if relation.source_id == node_id else relation.source_id
            )
        return [self.get_node(firm_id, neighbor_id) for neighbor_id in neighbor_ids]

    def explain(self, firm_id: str, relation_id: str) -> str:
        relation = self._relations.get(firm_id, relation_id)
        if relation is None:
            raise KeyError(relation_id)
        return relation.explanation or ""

    @staticmethod
    def _default_explanation(
        source: GraphNode, target: GraphNode, relation_type: RelationType
    ) -> str:
        verb = _RELATION_VERBS.get(relation_type, relation_type.value)
        return f"{source.label} {verb} {target.label}"
