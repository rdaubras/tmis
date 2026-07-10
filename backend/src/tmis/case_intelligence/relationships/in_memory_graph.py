from collections import defaultdict

from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode


class InMemoryCaseGraph:
    """Implements `CaseGraphPort` as an in-memory adjacency list.

    Sprint 4 scope: enough to prove the graph construction end-to-end. A
    graph database is a natural future replacement behind the same port,
    the same way `tmis.document_intelligence.knowledge.InMemoryKnowledgeGraph`
    is expected to be replaced (see docs/18-guide-knowledge-graph.md).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, CaseNode] = {}
        self._edges: list[CaseEdge] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node: CaseNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: CaseEdge) -> None:
        self._edges.append(edge)
        self._adjacency[edge.source_id].append(edge.target_id)

    def get_node(self, node_id: str) -> CaseNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[CaseNode]:
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
