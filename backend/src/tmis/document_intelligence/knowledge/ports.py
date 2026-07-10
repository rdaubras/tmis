from typing import Protocol

from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode


class KnowledgeGraphPort(Protocol):
    """Port implemented by every interchangeable knowledge graph backend.

    Deliberately independent from `tmis.ai.rag` (the vector store): a
    document's knowledge graph and its vector index answer different
    questions ("what is connected to what" vs. "what is semantically
    similar") and must be able to evolve separately (see
    docs/18-guide-knowledge-graph.md).
    """

    def add_node(self, node: KnowledgeNode) -> None: ...

    def add_edge(self, edge: KnowledgeEdge) -> None: ...

    def get_node(self, node_id: str) -> KnowledgeNode | None: ...

    def get_neighbors(self, node_id: str) -> list[KnowledgeNode]: ...
