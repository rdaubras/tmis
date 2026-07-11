"""Configurable, weighted risk matrix for a strategy.

Mirrors the shape of `ai_governance.confidence.GovernanceConfidenceWeights`
(normalizable named weights, always-explained result), reimplemented
locally rather than imported across bounded contexts — a strategic-
intelligence risk is not an AI-governance risk, even though both share
the weighted-factor pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RiskCriterion:
    name: str
    weight: float


DEFAULT_CRITERIA: tuple[RiskCriterion, ...] = (
    RiskCriterion("documentary_solidity", 0.3),
    RiskCriterion("reasoning_coherence", 0.25),
    RiskCriterion("evidence_dependency", 0.2),
    RiskCriterion("uncertainty", 0.15),
    RiskCriterion("requires_human_validation", 0.1),
)


@dataclass(frozen=True, slots=True)
class RiskMatrixResult:
    strategy_id: str
    score: float
    explanation: str
    factors: dict[str, float] = field(default_factory=dict)
