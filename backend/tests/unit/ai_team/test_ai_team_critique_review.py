from tmis.ai.schemas.agent import AgentOutput, ConfidenceLevel
from tmis.ai.schemas.citation import Citation
from tmis.ai_team.critique.engine import CritiqueEngine
from tmis.ai_team.review.engine import ReviewEngine
from tmis.ai_team.review.schemas import ReviewDecision

_SOLID_CITATION = Citation(
    source_id="code-civil", connector="legifrance", reference="Art. 1103", excerpt="..."
)


def test_critique_flags_short_output_as_incomplete() -> None:
    engine = CritiqueEngine()
    output = AgentOutput(result={"text": "ok"}, confidence=ConfidenceLevel.MEDIUM)

    critique = engine.critique("st-1", "agent-1", output)

    assert any("incomplète" in issue for issue in critique.issues)
    assert critique.is_clean is False


def test_critique_flags_low_confidence_without_warnings() -> None:
    engine = CritiqueEngine()
    output = AgentOutput(result={"text": "a" * 30}, confidence=ConfidenceLevel.LOW, warnings=[])

    critique = engine.critique("st-1", "agent-1", output)

    assert any("Confiance faible" in issue for issue in critique.issues)


def test_critique_suggests_citations_when_missing() -> None:
    engine = CritiqueEngine()
    output = AgentOutput(
        result={"text": "a" * 30}, confidence=ConfidenceLevel.HIGH, warnings=["note"]
    )

    critique = engine.critique("st-1", "agent-1", output)

    assert critique.is_clean is True
    assert any("référence" in s for s in critique.suggestions)


def test_critique_is_clean_for_a_solid_output() -> None:
    engine = CritiqueEngine()
    output = AgentOutput(
        result={"text": "a" * 30},
        confidence=ConfidenceLevel.HIGH,
        citations=[_SOLID_CITATION],
        warnings=["réserve mineure"],
    )

    critique = engine.critique("st-1", "agent-1", output)

    assert critique.is_clean is True
    assert critique.issues == ()
    assert critique.suggestions == ()


def test_review_approves_a_clean_critique() -> None:
    review = ReviewEngine(CritiqueEngine())
    output = AgentOutput(
        result={"text": "a" * 30},
        confidence=ConfidenceLevel.HIGH,
        citations=[_SOLID_CITATION],
        warnings=["réserve mineure"],
    )

    record = review.review("m1", "st-1", "agent-1", output)

    assert record.decision is ReviewDecision.APPROVED


def test_review_rejects_an_incomplete_output() -> None:
    review = ReviewEngine(CritiqueEngine())
    output = AgentOutput(result={"text": "ok"}, confidence=ConfidenceLevel.MEDIUM)

    record = review.review("m1", "st-1", "agent-1", output)

    assert record.decision is ReviewDecision.REJECTED


def test_review_requests_revision_for_a_non_fatal_issue() -> None:
    """Low confidence with no warnings is flagged as an issue (see
    `CritiqueEngine`) but is not the "incomplete output" issue that
    `ReviewEngine` treats as fatal — it should land on
    REVISION_REQUESTED, not REJECTED."""
    review = ReviewEngine(CritiqueEngine())
    output = AgentOutput(
        result={"text": "a" * 30}, confidence=ConfidenceLevel.LOW, warnings=[]
    )

    record = review.review("m1", "st-1", "agent-1", output)

    assert record.decision is ReviewDecision.REVISION_REQUESTED
