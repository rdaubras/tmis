from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    level: RiskLevel
    reasons: tuple[str, ...] = ()
    requires_step_up_mfa: bool = False
