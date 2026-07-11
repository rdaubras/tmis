from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.catalog import domain_expert_role, domain_expert_skill
from tmis.ai_team.capabilities.mission_templates import roles_for_case_type
from tmis.ai_team.capabilities.schemas import LegalDomain


def test_domain_expert_role_maps_known_domains() -> None:
    assert domain_expert_role(LegalDomain.DATA_PROTECTION) is AgentRole.GDPR_EXPERT
    assert domain_expert_role(LegalDomain.FISCAL) is AgentRole.TAX_EXPERT
    assert domain_expert_role(LegalDomain.SOCIAL) is AgentRole.SOCIAL_LAW_EXPERT


def test_domain_expert_role_is_none_for_general_domain() -> None:
    assert domain_expert_role(LegalDomain.GENERAL) is None
    assert domain_expert_role(LegalDomain.CIVIL) is None


def test_domain_expert_skill_matches_domain_expert_role() -> None:
    assert domain_expert_skill(LegalDomain.DATA_PROTECTION) == "gdpr"
    assert domain_expert_skill(LegalDomain.GENERAL) is None


def test_roles_for_case_type_deduplicates_repeated_roles() -> None:
    roles = roles_for_case_type("full_case_analysis")

    assert roles.count(AgentRole.DRAFTER) == 1
    assert AgentRole.DOCUMENT_ANALYST in roles
    assert AgentRole.QUALITY_CONTROLLER in roles


def test_roles_for_case_type_falls_back_to_default_for_unknown_type() -> None:
    assert roles_for_case_type("not-a-real-case-type") == roles_for_case_type(
        "full_case_analysis"
    )
