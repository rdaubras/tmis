from typing import Protocol

from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNode


class GraphNodeStorePort(Protocol):
    def save(self, node: GraphNode) -> None: ...

    def get(self, firm_id: str, node_id: str) -> GraphNode | None: ...

    def list_for_firm(self, firm_id: str) -> list[GraphNode]: ...


class GraphRelationStorePort(Protocol):
    def add(self, relation: KnowledgeRelation) -> None: ...

    def list_for_node(self, firm_id: str, node_id: str) -> list[KnowledgeRelation]: ...

    def get(self, firm_id: str, relation_id: str) -> KnowledgeRelation | None: ...
