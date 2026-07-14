from tmis.core.graph.adjacency_store import AdjacencyGraphStore
from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode


class InMemoryKnowledgeGraph:
    """Implements `KnowledgeGraphPort` as an in-memory adjacency list.

    Sprint 3 scope: enough to prove the graph construction end-to-end. A
    graph database (Neo4j or similar) is a natural future replacement
    behind the same port (see docs/18-guide-knowledge-graph.md).

    Composes `tmis.core.graph.AdjacencyGraphStore` (Sprint 25) for the
    actual storage mechanism rather than reimplementing it — see
    docs/145-architecture-knowledge-graph.md.
    """

    def __init__(self) -> None:
        self._store: AdjacencyGraphStore[KnowledgeNode, KnowledgeEdge] = AdjacencyGraphStore()

    def add_node(self, node: KnowledgeNode) -> None:
        self._store.add_node(node)

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self._store.add_edge(edge)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        return self._store.get_node(node_id)

    def get_neighbors(self, node_id: str) -> list[KnowledgeNode]:
        return self._store.get_neighbors(node_id)

    @property
    def node_count(self) -> int:
        return self._store.node_count

    @property
    def edge_count(self) -> int:
        return self._store.edge_count
