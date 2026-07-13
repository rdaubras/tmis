from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine
from tmis.identity_platform.tenant_context.engine import TenantContextEngine
from tmis.identity_platform.tenant_context.schemas import TenantProfile
from tmis.legal_copilot_framework.context_engine.schemas import CopilotContext


class ContextEngine:
    """Aggregates context from four already-existing engines rather
    than fetching/duplicating any of their state: `identity_platform.
    tenant_context.TenantContextEngine` (Sprint 19, firm context),
    `cabinet_knowledge.knowledge.KnowledgeSpace` (Sprint 12, relevant
    knowledge), `cabinet_knowledge.writing_style.WritingStyleEngine`
    (Sprint 12, drafting preferences), `ai_governance.policy_engine.
    PolicyEngine` (Sprint 15, active security/governance policies).
    """

    def __init__(
        self,
        tenant_context: TenantContextEngine,
        knowledge_space: KnowledgeSpace,
        writing_style: WritingStyleEngine,
        policy_engine: PolicyEngine,
    ) -> None:
        self._tenant_context = tenant_context
        self._knowledge_space = knowledge_space
        self._writing_style = writing_style
        self._policy_engine = policy_engine

    def build(
        self,
        firm_id: str,
        user_id: str,
        *,
        case_id: str | None = None,
        user_context: dict[str, str] | None = None,
        case_context: dict[str, str] | None = None,
        pieces: tuple[str, ...] = (),
        knowledge_tags: frozenset[str] = frozenset(),
    ) -> CopilotContext:
        tenant = self._tenant_context.get(firm_id)
        firm_context = self._firm_context(firm_id, tenant)
        relevant_ids = self._relevant_knowledge_ids(firm_id, knowledge_tags)
        writing_preferences = self._writing_preferences(firm_id, user_id)
        security_policies = tuple(
            f"{policy.type.value}: {policy.reason}"
            for policy in self._policy_engine.list_policies(firm_id)
            if policy.active
        )

        return CopilotContext(
            firm_id=firm_id,
            user_id=user_id,
            case_id=case_id,
            user_context=dict(user_context or {}),
            firm_context=firm_context,
            case_context=dict(case_context or {}),
            pieces=pieces,
            relevant_knowledge_ids=relevant_ids,
            security_policies=security_policies,
            writing_preferences=writing_preferences,
        )

    def _firm_context(self, firm_id: str, tenant: TenantProfile | None) -> dict[str, str]:
        if tenant is None:
            return {}
        return {
            "active": str(tenant.active),
            "max_users": str(tenant.quota.max_users),
            "max_ai_requests_per_day": str(tenant.quota.max_ai_requests_per_day),
            "display_name": tenant.branding.display_name if tenant.branding else firm_id,
        }

    def _relevant_knowledge_ids(
        self, firm_id: str, knowledge_tags: frozenset[str]
    ) -> tuple[str, ...]:
        objects = self._knowledge_space.list(firm_id, status=KnowledgeStatus.VALIDATED)
        if knowledge_tags:
            objects = [obj for obj in objects if knowledge_tags & obj.tags]
        return tuple(obj.id for obj in objects)

    def _writing_preferences(self, firm_id: str, user_id: str) -> dict[str, str]:
        profile = self._writing_style.get_or_create_profile(firm_id, user_id)
        return {
            "vocabulary": ",".join(profile.vocabulary),
            "favorite_expressions": ",".join(profile.favorite_expressions),
            "structure_preferences": ",".join(profile.structure_preferences),
            "signature_block": profile.signature_block,
        }
