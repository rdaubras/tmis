from tmis.ai_team.consensus.engine import ConsensusEngine
from tmis.ai_team.consensus.schemas import AgentPosition
from tmis.ai_team.negotiation.schemas import NegotiationOutcome, NegotiationRound


class NegotiationEngine:
    """Runs a structured confrontation round between disagreeing
    agents when `ConsensusEngine` flags a persistent divergence (see
    docs/56-guide-consensus-critique.md — Negotiation). This sprint's
    implementation is deliberately structural: it records each
    disagreeing agent's position as one negotiation round and reports
    whether the divergence resolved on its own (i.e. was not actually
    persistent once compared), rather than driving a live multi-round
    argument between agents — genuine adversarial re-prompting is a
    natural Sprint 12 extension, layered on top of this record-keeping
    without changing its shape."""

    def __init__(self, consensus_engine: ConsensusEngine) -> None:
        self._consensus_engine = consensus_engine

    def negotiate(self, topic: str, positions: list[AgentPosition]) -> NegotiationOutcome:
        result = self._consensus_engine.build_consensus(topic, positions)
        if not result.has_persistent_disagreement:
            return NegotiationOutcome(
                topic=topic, rounds=(), resolved=True, note="Consensus atteint."
            )

        rounds = tuple(
            NegotiationRound(
                round_number=1,
                agent_id=position.agent_id,
                position_text=position.text,
                rationale=f"Confiance déclarée: {position.confidence.value}.",
            )
            for position in positions
            if position.agent_id in result.disagreements
        )
        note = (
            f"Désaccord persistant entre {len(result.disagreements)} agent(s) "
            f"sur '{topic}' — soumis à validation humaine."
        )
        return NegotiationOutcome(topic=topic, rounds=rounds, resolved=False, note=note)
