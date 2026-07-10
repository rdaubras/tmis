from tmis.legal_reasoning.arguments.engine import HeuristicArgumentEngine
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


def _hypothesis(description: str, hypothesis_id: str = "h1") -> Hypothesis:
    return Hypothesis(id=hypothesis_id, description=description)


def _result(title: str, excerpt: str, connector: str = "codes") -> ResearchResult:
    return ResearchResult(
        id="r1",
        title=title,
        excerpt=excerpt,
        connector=connector,
        document_type="code",
        reference="ref-1",
        date=None,
        final_score=0.7,
    )


def test_build_creates_an_argument_when_result_overlaps_hypothesis() -> None:
    hypothesis = _hypothesis("Hypothèse favorable : le licenciement est fondé.")
    result = _result("Licenciement", "Le licenciement doit être justifié.")

    arguments = HeuristicArgumentEngine().build([hypothesis], [result])

    assert len(arguments) == 1
    assert arguments[0].hypothesis_id == hypothesis.id
    assert arguments[0].source_reference == "ref-1"
    assert arguments[0].source_connector == "codes"
    assert arguments[0].confidence == 0.7


def test_build_skips_unrelated_results() -> None:
    hypothesis = _hypothesis("Hypothèse favorable : le bail est résilié.")
    result = _result("Contrat", "Aucun rapport avec le sujet.")

    arguments = HeuristicArgumentEngine().build([hypothesis], [result])

    assert arguments == []


def test_build_can_support_multiple_hypotheses_from_one_result() -> None:
    h1 = _hypothesis("licenciement favorable", hypothesis_id="h1")
    h2 = _hypothesis("licenciement contraire", hypothesis_id="h2")
    result = _result("Licenciement", "licenciement justifié")

    arguments = HeuristicArgumentEngine().build([h1, h2], [result])

    hypothesis_ids = {a.hypothesis_id for a in arguments}
    assert hypothesis_ids == {h1.id, h2.id}
