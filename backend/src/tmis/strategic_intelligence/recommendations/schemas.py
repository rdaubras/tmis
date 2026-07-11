from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimilarStrategyRecommendation:
    """A past validated strategy resembling the current case — sourced
    from `learning/`'s outcome history, always explained."""

    strategy_id: str
    strategy_type: str
    explanation: str


@dataclass(frozen=True, slots=True)
class StrategicRecommendations:
    """Aggregates `cabinet_knowledge.recommendations` (existing
    validated knowledge) with similar past validated strategies. Two
    distinct sources, kept separate so a caller can tell which is
    which."""

    knowledge_recommendation_ids: tuple[str, ...]
    similar_strategies: tuple[SimilarStrategyRecommendation, ...]
