from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType, ValidationRequest
from tmis.workflow_automation.approval_gateway.ports import ApprovalPolicyStorePort
from tmis.workflow_automation.approval_gateway.schemas import ApprovalPolicy


class ApprovalGatewayEngine:
    """Gates critical actions behind human validation. Reuses
    `ai_governance.human_validation.HumanValidationEngine` directly
    rather than a fourth reimplementation of the approval-workflow
    pattern (after `cabinet_knowledge.validation`,
    `collaboration.approvals` and `ai_governance.human_validation`
    itself, already reused once in Sprint 16's `review/`). An action's
    `id` is passed as the engine's `production_id`."""

    def __init__(
        self, human_validation_engine: HumanValidationEngine, policy_store: ApprovalPolicyStorePort
    ) -> None:
        self._human_validation = human_validation_engine
        self._policy_store = policy_store

    def configure(self, firm_id: str, action_type: str, required: bool) -> ApprovalPolicy:
        policy = ApprovalPolicy(firm_id=firm_id, action_type=action_type, required=required)
        self._policy_store.set(policy)
        return policy

    def requires_approval(self, firm_id: str, action_type: str) -> bool:
        policy = self._policy_store.get(firm_id, action_type)
        return policy.required if policy is not None else False

    def request_approval(
        self, firm_id: str, action_id: str, requested_by: str, approver_ids: tuple[str, ...]
    ) -> ValidationRequest:
        return self._human_validation.request_simple(firm_id, action_id, requested_by, approver_ids)

    def decide(
        self,
        firm_id: str,
        request_id: str,
        approver_id: str,
        decision: ValidationDecisionType,
        comment: str | None = None,
    ) -> ValidationRequest:
        return self._human_validation.decide(firm_id, request_id, approver_id, decision, comment)

    def is_approved(self, firm_id: str, action_id: str) -> bool:
        return self._human_validation.is_validated(firm_id, action_id)
