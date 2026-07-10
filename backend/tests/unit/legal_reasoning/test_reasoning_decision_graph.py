from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.decision_graph.builder import ChainDecisionGraphBuilder
from tmis.legal_reasoning.decision_graph.schemas import DecisionNodeType
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


def test_build_creates_a_question_node_and_a_synthesis_node() -> None:
    graph = ChainDecisionGraphBuilder().build("question ?", [], [], [], [], [], "synthesis text")
    node_types = {n.type for n in graph.nodes}
    assert DecisionNodeType.QUESTION in node_types
    assert DecisionNodeType.SYNTHESIS in node_types


def test_build_links_question_to_each_hypothesis() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    graph = ChainDecisionGraphBuilder().build("q", [hypothesis], [], [], [], [], "s")

    edge = next(e for e in graph.edges if e.relation == "considers")
    assert edge.source_id == "question"
    assert edge.target_id == "hypothesis:h1"


def test_build_chains_hypothesis_argument_counter_argument() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    argument = Argument(
        id="a1", hypothesis_id="h1", claim="claim",
        source_connector="codes", source_reference="ref", excerpt="e",
    )
    counter = CounterArgument(
        id="c1", argument_id="a1", claim="counter",
        source_connector="doctrine", source_reference="ref2", excerpt="e2",
    )

    graph = ChainDecisionGraphBuilder().build("q", [hypothesis], [argument], [counter], [], [], "s")

    node_ids = {n.id for n in graph.nodes}
    assert "argument:a1" in node_ids
    assert "counter_argument:c1" in node_ids
    assert any(
        e.source_id == "argument:a1" and e.target_id == "counter_argument:c1" for e in graph.edges
    )


def test_build_includes_evidence_and_reference_nodes() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    evidence = ReasoningEvidenceLink(
        id="e1", fact_id="f1", document_id="d1", hypothesis_id="h1", argument_id=None,
        reliability_score=0.5,
    )

    graph = ChainDecisionGraphBuilder().build(
        "q", [hypothesis], [], [], [evidence], ["ref-1"], "s"
    )

    node_types = {n.type for n in graph.nodes}
    assert DecisionNodeType.EVIDENCE in node_types
    assert DecisionNodeType.REFERENCE in node_types


def test_build_links_every_hypothesis_to_synthesis() -> None:
    h1 = Hypothesis(id="h1", description="d1")
    h2 = Hypothesis(id="h2", description="d2")

    graph = ChainDecisionGraphBuilder().build("q", [h1, h2], [], [], [], [], "s")

    synthesis_edges = [e for e in graph.edges if e.target_id == "synthesis"]
    assert len(synthesis_edges) == 2
