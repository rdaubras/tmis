from dataclasses import dataclass, field
from enum import Enum


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(slots=True)
class Hypothesis:
    """One candidate legal reading of the question. Mutable: `confidence`
    and `status` are updated in place as the reasoning run progresses,
    but a `Hypothesis` is never overwritten or dropped — hypotheses
    coexist until an avocat validates or rejects one (see
    docs/25-legal-reasoning.md — Hypothesis Engine)."""

    id: str
    description: str
    supporting_fact_ids: tuple[str, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    status: HypothesisStatus = HypothesisStatus.PROPOSED
