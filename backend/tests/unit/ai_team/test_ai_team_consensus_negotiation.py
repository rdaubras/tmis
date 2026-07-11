from tmis.ai.schemas.agent import ConfidenceLevel
from tmis.ai_team.consensus.engine import ConsensusEngine
from tmis.ai_team.consensus.schemas import AgentPosition
from tmis.ai_team.negotiation.engine import NegotiationEngine


def test_consensus_is_high_for_near_identical_positions() -> None:
    engine = ConsensusEngine()
    positions = [
        AgentPosition("a1", "le preavis est de trois mois", ConfidenceLevel.HIGH),
        AgentPosition("a2", "le preavis est de trois mois environ", ConfidenceLevel.MEDIUM),
    ]

    result = engine.build_consensus("preavis", positions)

    assert result.agreement_ratio > 0.5
    assert result.disagreements == ()


def test_consensus_flags_a_clearly_divergent_position() -> None:
    engine = ConsensusEngine()
    positions = [
        AgentPosition(
            "a1", "resiliation immediate possible sans condition", ConfidenceLevel.HIGH
        ),
        AgentPosition(
            "a2", "neuf ans minimum requis avant toute resiliation", ConfidenceLevel.MEDIUM
        ),
    ]

    result = engine.build_consensus("duree", positions)

    assert result.has_persistent_disagreement is True
    assert "a2" in result.disagreements


def test_consensus_picks_the_most_agreed_with_position() -> None:
    engine = ConsensusEngine()
    positions = [
        AgentPosition("a1", "le contrat est resiliable avec preavis", ConfidenceLevel.HIGH),
        AgentPosition("a2", "le contrat est resiliable avec un preavis", ConfidenceLevel.MEDIUM),
        AgentPosition("a3", "aucun rapport avec la question posee ici", ConfidenceLevel.LOW),
    ]

    result = engine.build_consensus("resiliation", positions)

    assert result.consensus_text in {positions[0].text, positions[1].text}


def test_consensus_with_a_single_position_is_trivially_agreed() -> None:
    engine = ConsensusEngine()

    result = engine.build_consensus("topic", [AgentPosition("a1", "solo position")])

    assert result.agreement_ratio == 1.0
    assert result.consensus_text == "solo position"


def test_consensus_with_no_positions_is_empty() -> None:
    engine = ConsensusEngine()

    result = engine.build_consensus("topic", [])

    assert result.positions == ()
    assert result.consensus_text == ""


def test_negotiation_reports_resolved_when_consensus_is_reached() -> None:
    negotiation = NegotiationEngine(ConsensusEngine())
    positions = [
        AgentPosition("a1", "le preavis est de trois mois", ConfidenceLevel.HIGH),
        AgentPosition("a2", "le preavis est de trois mois", ConfidenceLevel.HIGH),
    ]

    outcome = negotiation.negotiate("preavis", positions)

    assert outcome.resolved is True
    assert outcome.rounds == ()


def test_negotiation_records_a_round_per_disagreeing_agent() -> None:
    negotiation = NegotiationEngine(ConsensusEngine())
    positions = [
        AgentPosition(
            "a1", "resiliation immediate possible sans condition", ConfidenceLevel.HIGH
        ),
        AgentPosition(
            "a2", "neuf ans minimum requis avant toute resiliation", ConfidenceLevel.MEDIUM
        ),
    ]

    outcome = negotiation.negotiate("duree", positions)

    assert outcome.resolved is False
    assert len(outcome.rounds) == 1
    assert outcome.rounds[0].agent_id == "a2"
    assert outcome.rounds[0].round_number == 1
