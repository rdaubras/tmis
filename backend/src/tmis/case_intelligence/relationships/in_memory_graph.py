from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode
from tmis.core.graph.adjacency_store import AdjacencyGraphStore


class InMemoryCaseGraph:
    """Implements `CaseGraphPort` as an in-memory adjacency list.

    Sprint 4 scope: enough to prove the graph construction end-to-end. A
    graph database is a natural future replacement behind the same port,
    the same way `tmis.document_intelligence.knowledge.InMemoryKnowledgeGraph`
    is expected to be replaced (see docs/18-guide-knowledge-graph.md).

    Composes `tmis.core.graph.AdjacencyGraphStore` (Sprint 25) for the
    actual storage mechanism rather than reimplementing it.
    """

    def __init__(self) -> None:
        self._store: AdjacencyGraphStore[CaseNode, CaseEdge] = AdjacencyGraphStore()

    def add_node(self, node: CaseNode) -> None:
        self._store.add_node(node)

    def add_edge(self, edge: CaseEdge) -> None:
        self._store.add_edge(edge)

    def get_node(self, node_id: str) -> CaseNode | None:
        return self._store.get_node(node_id)

    def get_neighbors(self, node_id: str) -> list[CaseNode]:
        return self._store.get_neighbors(node_id)

    @property
    def node_count(self) -> int:
        return self._store.node_count

    @property
    def edge_count(self) -> int:
        return self._store.edge_count
