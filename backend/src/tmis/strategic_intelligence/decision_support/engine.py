from tmis.strategic_intelligence.decision_support.schemas import (
    StrategyComparison,
    StrategyMetrics,
)


class DecisionSupportEngine:
    """Packages pre-computed metrics into a comparison table. Contains
    no scoring, weighting, or ranking logic whatsoever — comparison is
    presentation-only, by design."""

    def compare(self, metrics: list[StrategyMetrics]) -> StrategyComparison:
        return StrategyComparison(metrics=tuple(metrics))
