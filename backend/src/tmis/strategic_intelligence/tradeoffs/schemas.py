from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TradeoffAnalysis:
    """Pairwise comparison, one level deeper than
    `decision_support.StrategyComparison`'s N-way metrics table. Still
    never picks a winner — only lists each side's advantages and the
    risks they share."""

    strategy_a_id: str
    strategy_b_id: str
    advantages_a: tuple[str, ...] = field(default_factory=tuple)
    advantages_b: tuple[str, ...] = field(default_factory=tuple)
    shared_risks: tuple[str, ...] = field(default_factory=tuple)
