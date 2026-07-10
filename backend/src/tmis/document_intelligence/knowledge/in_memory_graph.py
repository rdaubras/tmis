from collections import defaultdict

from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode


class InMemoryKnowledgeGraph:
    """Implements `KnowledgeGraphPort` as an in-memory adjacency list.

    Sprint 3 scope: enough to prove the graph construction end-to-end. A
    graph database (Neo4j or similar) is a natural future replacement
    behind the same port (see docs/18-guide-knowledge-graph.md).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, KnowledgeNode] = {}
        self._edges: list[KnowledgeEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node: KnowledgeNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self._edges.append(edge)
        self._adjacency[edge.source_id].append(edge.target_id)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[KnowledgeNode]:
        return [
            self._nodes[target_id]
            for target_id in self._adjacency.get(node_id, [])
            if target_id in self._nodes
        ]

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)
