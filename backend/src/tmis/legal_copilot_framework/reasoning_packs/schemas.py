from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.ai_team.capabilities.schemas import LegalDomain


class ReasoningStrategyType(StrEnum):
    """The six strategy examples the sprint asks for."""

    QUALIFICATION = "qualification"
    RISK_ANALYSIS = "risk_analysis"
    CONTRADICTORY_ARGUMENTATION = "contradictory_argumentation"
    ALTERNATIVE_SEARCH = "alternative_search"
    JURISPRUDENCE_COMPARISON = "jurisprudence_comparison"
    CONSISTENCY_CHECK = "consistency_check"


@dataclass(frozen=True, slots=True)
class ReasoningPack:
    """A declaration, not an execution engine: it names which
    strategies a copilot uses and which stored `cabinet_knowledge.
    reasoning_patterns.ReasoningPattern` knowledge artifacts back
    them. The actual execution (qualification, argumentation,
    conflict detection, confidence scoring...) always runs through
    `legal_reasoning` — never reimplemented here, see the Sprint 24
    audit report (docs/reports/sprint-24-rapport-audit.md) on the two
    "reasoning pattern" concepts."""

    id: str
    name: str
    domain: LegalDomain
    version: int
    strategy_types: frozenset[ReasoningStrategyType]
    pattern_ids: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
