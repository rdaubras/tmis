from collections import defaultdict
from typing import Generic, Protocol, TypeVar


class _HasId(Protocol):
    @property
    def id(self) -> str: ...


class _HasEndpoints(Protocol):
    @property
    def source_id(self) -> str: ...

    @property
    def target_id(self) -> str: ...


NodeT = TypeVar("NodeT", bound=_HasId)
EdgeT = TypeVar("EdgeT", bound=_HasEndpoints)


class AdjacencyGraphStore(Generic[NodeT, EdgeT]):
    """The in-memory adjacency-list mechanism shared by every
    `*GraphPort` in-memory implementation (dict of nodes, list of
    edges, `defaultdict` adjacency list keyed by source id).

    Generic over the node/edge dataclass so each bounded-context graph
    (`CaseNode`/`CaseEdge`, `KnowledgeNode`/`KnowledgeEdge`, ...) keeps
    its own domain-typed vocabulary; this class only needs `node.id`
    and `edge.source_id`/`edge.target_id` to exist. Composed by
    delegation, never inherited, so each port implementation's public
    signature is untouched.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, NodeT] = {}
        self._edges: list[EdgeT] = []
        self._adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node: NodeT) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: EdgeT) -> None:
        self._edges.append(edge)
        self._adjacency[edge.source_id].append(edge.target_id)

    def get_node(self, node_id: str) -> NodeT | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[NodeT]:
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
