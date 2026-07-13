from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.ai_team.capabilities.schemas import LegalDomain


class CopilotValidationPolicyType(StrEnum):
    """The five examples the sprint asks for."""

    PARTNER_VALIDATION = "partner_validation"
    DOUBLE_VALIDATION = "double_validation"
    MANDATORY_HUMAN_REVIEW = "mandatory_human_review"
    MIN_CONFIDENCE = "min_confidence"
    ROLE_RESTRICTION = "role_restriction"


@dataclass(frozen=True, slots=True)
class CopilotValidationPolicy:
    """A copilot-scoped validation rule. Attaching it to a firm
    (`ValidationPolicyEngine.attach_to_firm`) creates a real
    `ai_governance.policy_engine.GovernancePolicy` — this dataclass is
    only the copilot-level declaration, never a second enforcement
    engine."""

    id: str
    name: str
    domain: LegalDomain
    type: CopilotValidationPolicyType
    description: str
    min_confidence: float | None = None
    required_role: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
