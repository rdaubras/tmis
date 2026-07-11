import re

from tmis.ai.schemas.agent import ConfidenceLevel
from tmis.ai_team.consensus.schemas import AgentPosition, ConsensusResult

_AGREEMENT_THRESHOLD = 0.4
_CONFIDENCE_RANK = {ConfidenceLevel.HIGH: 2, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.LOW: 0}


def _words(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"\w+", text.lower()))


def _similarity(a: str, b: str) -> float:
    """Jaccard similarity over word sets — a small, dependency-free
    heuristic (no embedding model call) good enough to flag whether
    two agents are broadly saying the same thing or not."""
    words_a, words_b = _words(a), _words(b)
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


class ConsensusEngine:
    """Compares several agents' positions on the same topic, produces
    an argued consensus, and flags persistent divergence (see
    docs/56-guide-consensus-critique.md — Consensus Engine). The
    "consensus" position is the one closest, on average, to every
    other position — a majority-lean, not a rewrite: this engine never
    generates new text, it only selects and explains."""

    def build_consensus(self, topic: str, positions: list[AgentPosition]) -> ConsensusResult:
        if not positions:
            return ConsensusResult(
                topic=topic, positions=(), agreement_ratio=1.0, consensus_text=""
            )
        if len(positions) == 1:
            only = positions[0]
            return ConsensusResult(
                topic=topic, positions=(only,), agreement_ratio=1.0, consensus_text=only.text
            )

        pairwise_scores: dict[str, list[float]] = {p.agent_id: [] for p in positions}
        for i, pos_a in enumerate(positions):
            for pos_b in positions[i + 1 :]:
                score = _similarity(pos_a.text, pos_b.text)
                pairwise_scores[pos_a.agent_id].append(score)
                pairwise_scores[pos_b.agent_id].append(score)

        average_scores = {
            agent_id: (sum(scores) / len(scores) if scores else 0.0)
            for agent_id, scores in pairwise_scores.items()
        }
        agreement_ratio = sum(average_scores.values()) / len(average_scores)

        best_agent_id = max(
            positions,
            key=lambda p: (average_scores[p.agent_id], _CONFIDENCE_RANK[p.confidence]),
        ).agent_id
        consensus_text = next(p.text for p in positions if p.agent_id == best_agent_id)

        disagreements = tuple(
            p.agent_id
            for p in positions
            if average_scores[p.agent_id] < _AGREEMENT_THRESHOLD and p.agent_id != best_agent_id
        )

        return ConsensusResult(
            topic=topic,
            positions=tuple(positions),
            agreement_ratio=agreement_ratio,
            consensus_text=consensus_text,
            disagreements=disagreements,
        )
