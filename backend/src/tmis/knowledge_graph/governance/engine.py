from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import (
    GovernancePolicy,
    GovernancePolicyType,
    PolicyEvaluation,
    PolicyEvaluationContext,
)
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus


class KnowledgeGraphGovernance:
    """Applies cabinet governance to federated/resolved knowledge
    graph data, composing two existing engines rather than building a
    third policy mechanism or a second knowledge lifecycle:

    - `PolicyEngine` for "who may see this resolved entity"
      (`RESTRICTED_ENTITY_VISIBILITY`).
    - `GovernanceEngine` for "is this cabinet knowledge object
      trustworthy enough to surface" (its existing DRAFT/IN_REVIEW/
      VALIDATED/OBSOLETE/ARCHIVED state machine).
    """

    def __init__(self, policy_engine: PolicyEngine, cabinet_governance: GovernanceEngine) -> None:
        self._policy_engine = policy_engine
        self._cabinet_governance = cabinet_governance

    def restrict_entity_visibility(
        self, firm_id: str, entity_id: str, required_role: str, reason: str
    ) -> GovernancePolicy:
        return self._policy_engine.create_policy(
            firm_id,
            GovernancePolicyType.RESTRICTED_ENTITY_VISIBILITY,
            reason,
            required_role=required_role,
            restricted_entity_id=entity_id,
        )

    def evaluate_entity_visibility(
        self, firm_id: str, production_id: str, entity_id: str, user_role: str | None
    ) -> PolicyEvaluation:
        context = PolicyEvaluationContext(
            firm_id=firm_id,
            production_id=production_id,
            entity_id=entity_id,
            user_role=user_role,
        )
        return self._policy_engine.evaluate(context)

    def is_knowledge_object_validated(self, firm_id: str, knowledge_object_id: str) -> bool:
        history = self._cabinet_governance.history(firm_id, knowledge_object_id)
        if not history:
            return False
        return history[-1].to_status is KnowledgeStatus.VALIDATED
