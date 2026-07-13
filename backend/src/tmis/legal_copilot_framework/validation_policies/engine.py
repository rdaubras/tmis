from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationRequest
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import (
    GovernancePolicy,
    GovernancePolicyType,
    PolicyEvaluation,
    PolicyEvaluationContext,
)
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.validation_policies.ports import (
    CopilotValidationPolicyStorePort,
)
from tmis.legal_copilot_framework.validation_policies.schemas import (
    CopilotValidationPolicy,
    CopilotValidationPolicyType,
)

_GOVERNANCE_TYPE_MAP: dict[CopilotValidationPolicyType, GovernancePolicyType] = {
    CopilotValidationPolicyType.PARTNER_VALIDATION: GovernancePolicyType.RESTRICTED_TO_ROLE,
    CopilotValidationPolicyType.MANDATORY_HUMAN_REVIEW: (
        GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT
    ),
    CopilotValidationPolicyType.MIN_CONFIDENCE: GovernancePolicyType.MIN_CONFIDENCE_THRESHOLD,
    CopilotValidationPolicyType.ROLE_RESTRICTION: GovernancePolicyType.RESTRICTED_TO_ROLE,
}
"""`DOUBLE_VALIDATION` is deliberately absent: it is a human-validation
*mode* (`HumanValidationEngine.request_multiple`), not a
`GovernancePolicyType` an automated `PolicyEngine.evaluate` call
checks — `attach_to_firm` raises for it, `request_validation` is the
right call instead."""


class ValidationPolicyEngine:
    """Composes `ai_governance.policy_engine.PolicyEngine` (per-firm
    automated policy evaluation) and `ai_governance.human_validation.
    HumanValidationEngine` (simple/multiple/hierarchical sign-off) —
    never a third validation mechanism. A copilot's validation
    policies are declared once here and attached to any firm that
    installs the copilot."""

    def __init__(
        self,
        store: CopilotValidationPolicyStorePort,
        policy_engine: PolicyEngine,
        human_validation: HumanValidationEngine,
    ) -> None:
        self._store = store
        self._policy_engine = policy_engine
        self._human_validation = human_validation

    def create_policy(
        self,
        policy_id: str,
        name: str,
        domain: LegalDomain,
        policy_type: CopilotValidationPolicyType,
        description: str,
        *,
        min_confidence: float | None = None,
        required_role: str | None = None,
    ) -> CopilotValidationPolicy:
        policy = CopilotValidationPolicy(
            id=policy_id,
            name=name,
            domain=domain,
            type=policy_type,
            description=description,
            min_confidence=min_confidence,
            required_role=required_role,
        )
        self._store.save(policy)
        return policy

    def get(self, policy_id: str) -> CopilotValidationPolicy:
        policy = self._store.get(policy_id)
        if policy is None:
            raise KeyError(policy_id)
        return policy

    def attach_to_firm(self, firm_id: str, policy_id: str) -> GovernancePolicy:
        policy = self.get(policy_id)
        governance_type = _GOVERNANCE_TYPE_MAP.get(policy.type)
        if governance_type is None:
            raise ValueError(
                f"{policy.type.value} has no automated PolicyEngine equivalent — "
                "use request_validation instead"
            )
        return self._policy_engine.create_policy(
            firm_id,
            governance_type,
            policy.description,
            min_confidence=policy.min_confidence,
            required_role=policy.required_role,
        )

    def request_validation(
        self,
        firm_id: str,
        production_id: str,
        requested_by: str,
        policy_id: str,
        approver_ids: tuple[str, ...],
    ) -> ValidationRequest:
        policy = self.get(policy_id)
        if policy.type is CopilotValidationPolicyType.DOUBLE_VALIDATION:
            return self._human_validation.request_multiple(
                firm_id, production_id, requested_by, approver_ids
            )
        if policy.type in (
            CopilotValidationPolicyType.PARTNER_VALIDATION,
            CopilotValidationPolicyType.MANDATORY_HUMAN_REVIEW,
        ):
            return self._human_validation.request_simple(
                firm_id, production_id, requested_by, approver_ids
            )
        raise ValueError(f"{policy.type.value} is evaluated automatically, not requested")

    def evaluate(self, context: PolicyEvaluationContext) -> PolicyEvaluation:
        return self._policy_engine.evaluate(context)
