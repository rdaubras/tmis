import uuid
from dataclasses import dataclass
from enum import StrEnum


class RiskCategory(StrEnum):
    """The sprint's explicit risk categories: manque de sources,
    sources contradictoires, informations anciennes, faible
    confiance, absence de validation humaine."""

    MISSING_SOURCES = "missing_sources"
    CONTRADICTORY_SOURCES = "contradictory_sources"
    OUTDATED_INFORMATION = "outdated_information"
    LOW_CONFIDENCE = "low_confidence"
    NO_HUMAN_VALIDATION = "no_human_validation"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def new_risk_finding_id() -> str:
    return f"risk-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class RiskFinding:
    """A single classified risk — always carries an `explanation`,
    never a bare severity flag."""

    id: str
    category: RiskCategory
    severity: RiskSeverity
    description: str
    explanation: str
