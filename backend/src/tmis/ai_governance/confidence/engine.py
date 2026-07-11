from tmis.ai_governance.confidence.schemas import (
    GovernanceConfidenceScore,
    GovernanceConfidenceWeights,
)


class GovernanceConfidenceEngine:
    """Decomposes an AI production's confidence into the sprint's five
    named factors. Deliberately takes pre-computed factor values
    rather than reaching into `legal_reasoning`/`ai_team`/`ai_fabric`
    itself — the caller (typically `ai_governance.quality` or the
    top-level facade) is responsible for deriving each factor from the
    relevant engine (provenance completeness for source quality,
    `ai_fabric.evaluation.ResponseEvaluator.coherence_score` for
    reasoning coherence, `human_validation` status, multi-agent
    consensus agreement ratio, `ai_fabric.quality_optimizer`
    stability), keeping this module free of cross-context imports."""

    def score(
        self,
        production_id: str,
        *,
        source_quality: float,
        reasoning_coherence: float,
        human_validation: float,
        multi_agent_consensus: float,
        model_stability: float,
        weights: GovernanceConfidenceWeights | None = None,
    ) -> GovernanceConfidenceScore:
        effective_weights = (weights or GovernanceConfidenceWeights()).normalized()

        value = (
            effective_weights.source_quality * source_quality
            + effective_weights.reasoning_coherence * reasoning_coherence
            + effective_weights.human_validation * human_validation
            + effective_weights.multi_agent_consensus * multi_agent_consensus
            + effective_weights.model_stability * model_stability
        )

        explanation = (
            f"qualité des sources {source_quality:.2f}, cohérence du raisonnement "
            f"{reasoning_coherence:.2f}, validation humaine {human_validation:.2f}, "
            f"consensus multi-agents {multi_agent_consensus:.2f}, stabilité des modèles "
            f"{model_stability:.2f}."
        )
        return GovernanceConfidenceScore(
            production_id=production_id,
            value=value,
            explanation=explanation,
            factors={
                "source_quality": source_quality,
                "reasoning_coherence": reasoning_coherence,
                "human_validation": human_validation,
                "multi_agent_consensus": multi_agent_consensus,
                "model_stability": model_stability,
            },
        )
