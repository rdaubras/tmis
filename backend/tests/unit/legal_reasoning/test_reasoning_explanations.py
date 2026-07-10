from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict, ConflictType
from tmis.legal_reasoning.explanations.engine import ReasoningExplanationEngine
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


def test_build_always_warns_this_is_not_a_legal_opinion() -> None:
    explanation = ReasoningExplanationEngine().build("question ?", [], [], [], [], {})
    assert any("avis juridique" in limitation for limitation in explanation.limitations)


def test_build_lists_hypotheses_considered() -> None:
    hypothesis = Hypothesis(id="h1", description="Hypothèse test")
    explanation = ReasoningExplanationEngine().build("q", [hypothesis], [], [], [], {})
    assert "Hypothèse test" in explanation.hypotheses_considered


def test_build_flags_low_confidence_hypotheses() -> None:
    hypothesis = Hypothesis(id="h1", description="Hypothèse test")
    scores = {"h1": ConfidenceScore(hypothesis_id="h1", value=0.1, explanation="low")}
    explanation = ReasoningExplanationEngine().build("q", [hypothesis], [], [], [], scores)
    assert any("Confiance faible" in limitation for limitation in explanation.limitations)


def test_build_mentions_unresolved_conflicts() -> None:
    conflict = Conflict(
        id="c1", type=ConflictType.DUPLICATE, description="d", explanation="e", involved_ids=()
    )
    explanation = ReasoningExplanationEngine().build("q", [], [], [], [conflict], {})
    assert any("conflit" in limitation.lower() for limitation in explanation.limitations)


def test_build_collects_unique_references_from_hypotheses() -> None:
    h1 = Hypothesis(id="h1", description="d1", references=("ref-a", "ref-b"))
    h2 = Hypothesis(id="h2", description="d2", references=("ref-b",))
    explanation = ReasoningExplanationEngine().build("q", [h1, h2], [], [], [], {})
    assert explanation.references == ("ref-a", "ref-b")


def test_reasoning_steps_mention_the_question() -> None:
    explanation = ReasoningExplanationEngine().build("Ma question ?", [], [], [], [], {})
    assert any("Ma question ?" in step for step in explanation.reasoning_steps)
