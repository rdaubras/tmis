"""Schemas for cross-hypothesis strategic options.

`Strategy` operates at a different scope than
`tmis.legal_reasoning.strategy.StrategyOption`: the latter proposes one
option per hypothesis, while `Strategy` proposes a whole approach
(negotiation, litigation, transactional, procedural...) that may draw on
several hypotheses at once. Like every recommendation-shaped object in
TMIS, a `Strategy` never claims to be a decision — it is always
accompanied by its hypotheses, its limitations and a confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True, slots=True)
class Strategy:
    """One possible strategic approach among several coexisting options.

    Never a recommendation: the SLAI always returns every strategy it
    can build, along with its hypotheses, missing evidence and
    limitations. The choice belongs to the avocat.
    """

    id: str
    case_id: str
    strategy_type: str
    objective: str
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    main_arguments: tuple[str, ...] = field(default_factory=tuple)
    counter_arguments: tuple[str, ...] = field(default_factory=tuple)
    available_evidence: tuple[str, ...] = field(default_factory=tuple)
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)
    recommended_steps: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    limitations: tuple[str, ...] = field(default_factory=tuple)


DEFAULT_STRATEGY_TYPES: tuple[str, ...] = (
    "Négociation amiable",
    "Action prud'homale",
    "Stratégie transactionnelle",
    "Stratégie procédurale",
)
