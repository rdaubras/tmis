from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StrategyMetrics:
    strategy_id: str
    strategy_type: str
    confidence: float
    coverage: float
    risk_score: float
    effort: float
    estimated_duration_days: int


@dataclass(frozen=True, slots=True)
class StrategyComparison:
    """A side-by-side metrics table across strategies. Deliberately has
    no "recommended" or "best" field — "le moteur ne choisit jamais à
    la place de l'avocat" (sprint requirement). The disclaimer is
    always attached so no consumer of this object can present it as a
    ranking."""

    metrics: tuple[StrategyMetrics, ...] = field(default_factory=tuple)
    disclaimer: str = (
        "Ce tableau compare des métriques ; il ne désigne aucune stratégie "
        "comme recommandée. Le choix revient exclusivement à l'avocat."
    )
