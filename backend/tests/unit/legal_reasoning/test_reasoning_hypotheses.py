from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.hypotheses.engine import HeuristicHypothesisEngine
from tmis.legal_reasoning.hypotheses.schemas import HypothesisStatus
from tmis.legal_research.search.schemas import ResearchResult


def _fact(description: str) -> Fact:
    return Fact(id="fact-1", description=description, confidence=0.8)


def _result(reference: str) -> ResearchResult:
    return ResearchResult(
        id="r1",
        title="Title",
        excerpt="Excerpt",
        connector="codes",
        document_type="code",
        reference=reference,
        date=None,
    )


def test_generate_returns_at_least_two_coexisting_hypotheses() -> None:
    hypotheses = HeuristicHypothesisEngine().generate("Le licenciement est-il fondé ?", [], [])
    assert len(hypotheses) == 2
    ids = {h.id for h in hypotheses}
    assert len(ids) == 2


def test_generated_hypotheses_start_as_proposed() -> None:
    hypotheses = HeuristicHypothesisEngine().generate("question ?", [], [])
    assert all(h.status == HypothesisStatus.PROPOSED for h in hypotheses)


def test_generate_links_facts_sharing_keywords_with_the_question() -> None:
    fact = _fact("Le licenciement a été notifié le 3 mars.")
    hypotheses = HeuristicHypothesisEngine().generate(
        "Le licenciement est-il fondé ?", [fact], []
    )
    affirmative = hypotheses[0]
    assert fact.id in affirmative.supporting_fact_ids


def test_generate_does_not_link_unrelated_facts() -> None:
    fact = _fact("Le bail commercial a été signé en 2019.")
    hypotheses = HeuristicHypothesisEngine().generate(
        "Le licenciement est-il fondé ?", [fact], []
    )
    assert fact.id not in hypotheses[0].supporting_fact_ids


def test_generate_attaches_references_from_research_results() -> None:
    result = _result("civ-1240")
    hypotheses = HeuristicHypothesisEngine().generate("question ?", [], [result])
    assert "civ-1240" in hypotheses[0].references
    assert "civ-1240" in hypotheses[1].references
