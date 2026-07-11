from tmis.cabinet_knowledge.recommendations.engine import RecommendationEngine
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.strategic_intelligence.recommendations.schemas import (
    SimilarStrategyRecommendation,
    StrategicRecommendations,
)


class StrategicRecommendationEngine:
    """Composes `cabinet_knowledge.recommendations.RecommendationEngine`
    (already explainable, validated-knowledge-only) as the primary
    source, plus "similar past validated strategies" supplied by the
    caller. Takes `similar_strategies` as a parameter rather than
    importing `learning/` directly — same decoupled-input convention
    used across this sprint — so this engine stays testable without a
    learning-history fixture."""

    def __init__(self, cabinet_recommendation_engine: RecommendationEngine) -> None:
        self._cabinet_recommendations = cabinet_recommendation_engine

    def recommend(
        self,
        firm_id: str,
        context: RecommendationContext,
        similar_strategies: tuple[SimilarStrategyRecommendation, ...] = (),
        limit: int = 5,
    ) -> StrategicRecommendations:
        knowledge_recommendations = self._cabinet_recommendations.recommend(
            firm_id, context, limit
        )
        return StrategicRecommendations(
            knowledge_recommendation_ids=tuple(
                r.knowledge_object_id for r in knowledge_recommendations
            ),
            similar_strategies=similar_strategies,
        )
