from tmis.ai_team.agents.catalog import default_descriptors
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.registry.store import InMemoryAgentRegistry
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.teams.schemas import MissionComplexity
from tmis.ai_team.teams.store import InMemoryTeamStore


def _registry() -> InMemoryAgentRegistry:
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)
    return registry


def _builder() -> TeamBuilder:
    return TeamBuilder(_registry(), InMemoryTeamStore())


def test_build_team_default_is_full_case_analysis() -> None:
    team = _builder().build_team()

    assert len(team.member_agent_ids) == 6
    assert team.is_custom is False


def test_build_team_adds_domain_expert_when_relevant() -> None:
    team = _builder().build_team(domain=LegalDomain.FISCAL, case_type="standard_analysis")

    assert "agent-tax-expert" in team.member_agent_ids


def test_build_team_skips_domain_expert_for_low_complexity() -> None:
    team = _builder().build_team(
        domain=LegalDomain.FISCAL,
        complexity=MissionComplexity.LOW,
        case_type="standard_analysis",
    )

    assert "agent-tax-expert" not in team.member_agent_ids


def test_build_team_never_adds_a_domain_expert_for_general_domain() -> None:
    team = _builder().build_team(domain=LegalDomain.GENERAL, case_type="full_case_analysis")

    domain_expert_ids = {"agent-gdpr-expert", "agent-tax-expert", "agent-social-law-expert"}
    assert domain_expert_ids.isdisjoint(team.member_agent_ids)


def test_build_custom_team_preserves_given_agent_order() -> None:
    team = _builder().build_custom_team("Mon équipe", ["agent-drafter", "agent-verifier"])

    assert team.member_agent_ids == ["agent-drafter", "agent-verifier"]
    assert team.is_custom is True


def test_build_team_with_tight_budget_trims_agents() -> None:
    team = _builder().build_team(case_type="full_case_analysis", target_cost_usd=0.005)

    assert len(team.member_agent_ids) == 1


def test_build_team_with_generous_budget_keeps_full_template() -> None:
    team = _builder().build_team(case_type="quick_review", target_cost_usd=1000.0)

    assert len(team.member_agent_ids) == 2


def test_every_predefined_case_type_produces_a_team_matching_planner_roles() -> None:
    from tmis.ai_team.planner.engine import Planner

    planner = Planner()
    for case_type in ("quick_review", "drafting_only", "standard_analysis", "full_case_analysis"):
        team = _builder().build_team(case_type=case_type)
        plan = planner.decompose(case_type=case_type)
        registry = _registry()
        team_roles = {registry.get(a).role for a in team.member_agent_ids}  # type: ignore[union-attr]
        plan_roles = {st.assigned_role for st in plan.sub_tasks}
        assert plan_roles <= team_roles, f"{case_type}: plan needs roles the team doesn't have"
