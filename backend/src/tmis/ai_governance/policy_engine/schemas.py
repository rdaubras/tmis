import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class GovernancePolicyType(StrEnum):
    """The sprint's explicit governance policy examples: validation
    obligatoire avant export, seuil minimal de confiance, interdiction
    de certains modèles, obligation de citations, relecture
    obligatoire pour certains types de dossiers. Distinct from
    `tmis.ai_fabric.policies.PolicyType`, which governs which MODEL
    may be used — this enum governs whether a produced DECISION/OUTPUT
    may be exported or considered final."""

    MANDATORY_VALIDATION_BEFORE_EXPORT = "mandatory_validation_before_export"
    MIN_CONFIDENCE_THRESHOLD = "min_confidence_threshold"
    FORBIDDEN_MODEL = "forbidden_model"
    MANDATORY_CITATIONS = "mandatory_citations"
    MANDATORY_REVIEW_FOR_CASE_TYPE = "mandatory_review_for_case_type"
    # Added in Sprint 24 (Legal Copilot Framework) for its Validation
    # Policies ("restrictions selon le rôle") — reuses identity_platform's
    # role vocabulary via `required_role` rather than a parallel check.
    RESTRICTED_TO_ROLE = "restricted_to_role"


def new_governance_policy_id() -> str:
    return f"gpol-{uuid.uuid4()}"


@dataclass(slots=True)
class GovernancePolicy:
    """Configurable per cabinet (`firm_id`) — the sprint's "les
    politiques sont configurables par cabinet"."""

    id: str
    firm_id: str
    type: GovernancePolicyType
    reason: str
    min_confidence: float | None = None
    forbidden_model_name: str | None = None
    case_type: str | None = None
    required_role: str | None = None
    active: bool = True


def new_policy_evaluation_id() -> str:
    return f"polres-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class PolicyEvaluationContext:
    """Everything the engine needs to evaluate one production against
    a firm's configured policies."""

    firm_id: str
    production_id: str
    is_export: bool = False
    confidence_value: float | None = None
    model_names_used: tuple[str, ...] = ()
    citation_count: int | None = None
    case_type: str | None = None
    human_validated: bool = False
    user_role: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """A policy evaluation outcome, always explained — mirrors
    `tmis.ai_fabric.governance.PolicyDecision`'s shape."""

    id: str
    firm_id: str
    production_id: str
    allowed: bool
    reasons: tuple[str, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
