from tmis.ai_fabric.consensus.schemas import ConsensusOutcome, ModelPosition
from tmis.ai_fabric.evaluation.engine import jaccard_similarity

_AGREEMENT_THRESHOLD = 0.4


class ConsensusEngine:
    """The sprint's "CONSENSUS ENGINE": when several models disagree,
    produces an argued synthesis while *preserving* the divergences
    rather than silently discarding them — mirrors
    `tmis.ai_team.consensus.ConsensusEngine`'s Jaccard-similarity
    approach, but operates on raw `ModelPosition`s from the Fabric
    router instead of agent-produced `AgentOutput`s, and ranks by the
    model's `quality_score` (from `tmis.ai_fabric.critic`) instead of
    an agent's declared confidence level."""

    def build_consensus(self, topic: str, positions: list[ModelPosition]) -> ConsensusOutcome:
        if not positions:
            return ConsensusOutcome(
                topic=topic, positions=(), agreement_ratio=1.0, synthesis=""
            )
        if len(positions) == 1:
            only = positions[0]
            return ConsensusOutcome(
                topic=topic, positions=(only,), agreement_ratio=1.0, synthesis=only.text
            )

        pairwise_scores: dict[str, list[float]] = {p.model_name: [] for p in positions}
        for i, pos_a in enumerate(positions):
            for pos_b in positions[i + 1 :]:
                score = jaccard_similarity(pos_a.text, pos_b.text)
                pairwise_scores[pos_a.model_name].append(score)
                pairwise_scores[pos_b.model_name].append(score)

        average_scores = {
            model_name: (sum(scores) / len(scores) if scores else 0.0)
            for model_name, scores in pairwise_scores.items()
        }
        agreement_ratio = sum(average_scores.values()) / len(average_scores)

        best = max(positions, key=lambda p: (average_scores[p.model_name], p.quality_score))

        divergences = tuple(
            f"{p.model_name} : {p.text}"
            for p in positions
            if average_scores[p.model_name] < _AGREEMENT_THRESHOLD
            and p.model_name != best.model_name
        )

        return ConsensusOutcome(
            topic=topic,
            positions=tuple(positions),
            agreement_ratio=agreement_ratio,
            synthesis=best.text,
            divergences=divergences,
        )
