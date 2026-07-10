from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode, CaseNodeType


def test_add_and_get_node() -> None:
    graph = InMemoryCaseGraph()
    node = CaseNode(id="doc-1", type=CaseNodeType.DOCUMENT, label="bail.txt")
    graph.add_node(node)
    assert graph.get_node("doc-1") == node


def test_get_unknown_node_returns_none() -> None:
    assert InMemoryCaseGraph().get_node("missing") is None


def test_get_neighbors_follows_edges() -> None:
    graph = InMemoryCaseGraph()
    graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    graph.add_node(CaseNode(id="doc-1", type=CaseNodeType.DOCUMENT, label="bail.txt"))
    graph.add_edge(CaseEdge(source_id="actor-1", target_id="doc-1", relation="mentioned_in"))

    neighbors = graph.get_neighbors("actor-1")

    assert neighbors == [CaseNode(id="doc-1", type=CaseNodeType.DOCUMENT, label="bail.txt")]


def test_node_and_edge_counts() -> None:
    graph = InMemoryCaseGraph()
    graph.add_node(CaseNode(id="a", type=CaseNodeType.ACTOR, label="a"))
    graph.add_node(CaseNode(id="b", type=CaseNodeType.DOCUMENT, label="b"))
    graph.add_edge(CaseEdge(source_id="a", target_id="b", relation="mentioned_in"))

    assert graph.node_count == 2
    assert graph.edge_count == 1
