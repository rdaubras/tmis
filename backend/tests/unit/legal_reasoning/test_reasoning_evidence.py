from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.evidence.engine import HeuristicEvidenceEngine
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


def test_link_connects_fact_document_and_hypothesis() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=("f1",))
    fact = Fact(
        id="f1",
        description="fact",
        confidence=0.8,
        source_document_ids={"doc-1"},
    )

    links = HeuristicEvidenceEngine().link([hypothesis], [], [fact])

    assert len(links) == 1
    link = links[0]
    assert link.fact_id == "f1"
    assert link.document_id == "doc-1"
    assert link.hypothesis_id == "h1"


def test_link_attaches_the_first_related_argument() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=("f1",))
    fact = Fact(id="f1", description="fact", confidence=0.8, source_document_ids={"doc-1"})
    argument = Argument(
        id="a1",
        hypothesis_id="h1",
        claim="claim",
        source_connector="codes",
        source_reference="ref",
        excerpt="excerpt",
    )

    links = HeuristicEvidenceEngine().link([hypothesis], [argument], [fact])

    assert links[0].argument_id == "a1"


def test_reliability_decreases_with_contradictions() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=("f1", "f2"))
    strong_fact = Fact(
        id="f1", description="strong", confidence=0.9, confirming_document_ids={"d1", "d2"}
    )
    weak_fact = Fact(
        id="f2", description="weak", confidence=0.9, contradicting_document_ids={"d3", "d4"}
    )

    links = HeuristicEvidenceEngine().link([hypothesis], [], [strong_fact, weak_fact])

    reliability_by_fact = {link.fact_id: link.reliability_score for link in links}
    assert reliability_by_fact["f1"] > reliability_by_fact["f2"]


def test_link_handles_facts_without_source_documents() -> None:
    hypothesis = Hypothesis(id="h1", description="desc", supporting_fact_ids=("f1",))
    fact = Fact(id="f1", description="fact", confidence=0.5)

    links = HeuristicEvidenceEngine().link([hypothesis], [], [fact])

    assert len(links) == 1
    assert links[0].document_id is None
