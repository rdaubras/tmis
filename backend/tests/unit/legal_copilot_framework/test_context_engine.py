from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import GovernancePolicyType
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine
from tmis.identity_platform.tenant_context.engine import TenantContextEngine
from tmis.identity_platform.tenant_context.schemas import TenantBranding
from tmis.identity_platform.tenant_context.store import InMemoryTenantProfileStore
from tmis.legal_copilot_framework.context_engine.engine import ContextEngine

FIRM = "firm-a"
USER = "user-1"


def _engine() -> tuple[ContextEngine, KnowledgeSpace, TenantContextEngine, PolicyEngine]:
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    tenant_context = TenantContextEngine(InMemoryTenantProfileStore())
    writing_style = WritingStyleEngine(space)
    policy_engine = PolicyEngine(InMemoryGovernancePolicyStore())
    engine = ContextEngine(tenant_context, space, writing_style, policy_engine)
    return engine, space, tenant_context, policy_engine


def test_build_returns_empty_firm_context_for_unknown_firm() -> None:
    engine, _, _, _ = _engine()
    context = engine.build(FIRM, USER)

    assert context.firm_context == {}
    assert context.firm_id == FIRM
    assert context.user_id == USER


def test_build_includes_firm_context_when_tenant_is_provisioned() -> None:
    engine, _, tenant_context, _ = _engine()
    tenant_context.provision(FIRM, branding=TenantBranding(display_name="Cabinet Demo"))

    context = engine.build(FIRM, USER)

    assert context.firm_context["display_name"] == "Cabinet Demo"


def test_build_only_returns_validated_knowledge_matching_tags() -> None:
    engine, space, _, _ = _engine()
    validated = space.create(
        FIRM, KnowledgeType.PLAYBOOK, "Validated", {}, "author", tags=frozenset({"civil"})
    )
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    governance.transition(FIRM, validated.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, validated.id, KnowledgeStatus.VALIDATED, actor="a")
    space.create(FIRM, KnowledgeType.PLAYBOOK, "Draft", {}, "author", tags=frozenset({"civil"}))

    context = engine.build(FIRM, USER, knowledge_tags=frozenset({"civil"}))

    assert context.relevant_knowledge_ids == (validated.id,)


def test_build_includes_active_security_policies() -> None:
    engine, _, _, policy_engine = _engine()
    policy_engine.create_policy(FIRM, GovernancePolicyType.MIN_CONFIDENCE_THRESHOLD, "Seuil requis")

    context = engine.build(FIRM, USER)

    assert len(context.security_policies) == 1
    assert "Seuil requis" in context.security_policies[0]


def test_build_includes_writing_preferences() -> None:
    engine, _, _, _ = _engine()

    context = engine.build(FIRM, USER)

    assert "vocabulary" in context.writing_preferences


def test_build_passes_through_case_context_and_pieces() -> None:
    engine, _, _, _ = _engine()

    context = engine.build(
        FIRM, USER, case_id="case-1", case_context={"type": "litige"}, pieces=("piece-1",)
    )

    assert context.case_id == "case-1"
    assert context.case_context == {"type": "litige"}
    assert context.pieces == ("piece-1",)
