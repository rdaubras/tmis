from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.engine import HeuristicCounterArgumentEngine
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


def _argument(hypothesis_id: str = "h1", connector: str = "codes") -> Argument:
    return Argument(
        id="a1",
        hypothesis_id=hypothesis_id,
        claim="claim",
        source_connector=connector,
        source_reference="ref-1",
        excerpt="excerpt",
    )


def _result(connector: str, ref: str = "ref-2") -> ResearchResult:
    return ResearchResult(
        id="r2",
        title="Alt title",
        excerpt="alt excerpt",
        connector=connector,
        document_type="doctrine",
        reference=ref,
        date=None,
        final_score=0.4,
    )


def test_build_prefers_a_contradicting_fact_when_available() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=("f1",))
    fact = Fact(
        id="f1",
        description="Le fait contesté",
        confidence=0.9,
        contradicting_document_ids={"doc-2"},
    )
    argument = _argument(hypothesis_id="h1")

    counters = HeuristicCounterArgumentEngine().build([argument], [hypothesis], [fact], [])

    assert len(counters) == 1
    assert counters[0].source_connector == "case_facts"
    assert counters[0].source_reference == "f1"
    assert counters[0].argument_id == argument.id


def test_build_falls_back_to_a_contrasting_research_result() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=())
    argument = _argument(hypothesis_id="h1", connector="codes")
    alt_result = _result(connector="doctrine")

    counters = HeuristicCounterArgumentEngine().build(
        [argument], [hypothesis], [], [alt_result]
    )

    assert len(counters) == 1
    assert counters[0].source_connector == "doctrine"
    assert counters[0].argument_id == argument.id


def test_build_does_not_use_same_connector_result_as_counter() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=())
    argument = _argument(hypothesis_id="h1", connector="codes")
    same_connector_result = _result(connector="codes")

    counters = HeuristicCounterArgumentEngine().build(
        [argument], [hypothesis], [], [same_connector_result]
    )

    assert counters == []


def test_build_returns_nothing_when_no_hypothesis_matches() -> None:
    argument = _argument(hypothesis_id="unknown")
    counters = HeuristicCounterArgumentEngine().build([argument], [], [], [])
    assert counters == []
