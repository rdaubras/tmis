from typing import Protocol

from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode


class CaseGraphPort(Protocol):
    """Port implemented by every interchangeable case-relationship graph
    backend (see docs/19-case-intelligence.md)."""

    def add_node(self, node: CaseNode) -> None: ...

    def add_edge(self, edge: CaseEdge) -> None: ...

    def get_node(self, node_id: str) -> CaseNode | None: ...

    def get_neighbors(self, node_id: str) -> list[CaseNode]: ...
