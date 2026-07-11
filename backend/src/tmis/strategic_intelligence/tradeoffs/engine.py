from tmis.strategic_intelligence.tradeoffs.schemas import TradeoffAnalysis


class TradeoffEngine:
    """Pure set arithmetic on pre-computed advantages/risks — never
    picks a winner, only structures the comparison."""

    def compare(
        self,
        strategy_a_id: str,
        strategy_b_id: str,
        *,
        advantages_a: tuple[str, ...] = (),
        advantages_b: tuple[str, ...] = (),
        risks_a: tuple[str, ...] = (),
        risks_b: tuple[str, ...] = (),
    ) -> TradeoffAnalysis:
        shared_risks = tuple(sorted(set(risks_a) & set(risks_b)))
        return TradeoffAnalysis(
            strategy_a_id=strategy_a_id,
            strategy_b_id=strategy_b_id,
            advantages_a=advantages_a,
            advantages_b=advantages_b,
            shared_risks=shared_risks,
        )
