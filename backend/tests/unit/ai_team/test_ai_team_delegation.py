from tmis.ai_team.agents.catalog import default_descriptors
from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import TaskType
from tmis.ai_team.delegation.engine import DelegationEngine
from tmis.ai_team.planner.schemas import SubTask
from tmis.ai_team.registry.store import InMemoryAgentRegistry
from tmis.ai_team.teams.schemas import Team


def _registry() -> InMemoryAgentRegistry:
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)
    return registry


def test_assign_agent_matches_role_within_the_team() -> None:
    registry = _registry()
    engine = DelegationEngine(registry)
    team = Team(id="t1", name="Team", member_agent_ids=["agent-drafter", "agent-verifier"])
    sub_task = SubTask(
        id="st-1", task_type=TaskType.DRAFTING, assigned_role=AgentRole.DRAFTER, description="d"
    )

    agent_id = engine.assign_agent("m1", sub_task, team)

    assert agent_id == "agent-drafter"


def test_assign_agent_returns_none_when_team_lacks_the_role() -> None:
    registry = _registry()
    engine = DelegationEngine(registry)
    team = Team(id="t1", name="Team", member_agent_ids=["agent-verifier"])
    sub_task = SubTask(
        id="st-1", task_type=TaskType.DRAFTING, assigned_role=AgentRole.DRAFTER, description="d"
    )

    agent_id = engine.assign_agent("m1", sub_task, team)

    assert agent_id is None


def test_assign_agent_records_every_decision() -> None:
    registry = _registry()
    engine = DelegationEngine(registry)
    team = Team(id="t1", name="Team", member_agent_ids=["agent-verifier"])
    sub_task = SubTask(
        id="st-1",
        task_type=TaskType.VERIFICATION,
        assigned_role=AgentRole.VERIFIER,
        description="d",
    )

    engine.assign_agent("m1", sub_task, team)
    engine.assign_agent("m2", sub_task, team)

    assert len(engine.records_for_mission("m1")) == 1
    assert len(engine.records_for_mission("m2")) == 1


def test_assign_agent_ignores_team_members_not_in_the_registry() -> None:
    registry = _registry()
    engine = DelegationEngine(registry)
    team = Team(id="t1", name="Team", member_agent_ids=["agent-unknown", "agent-drafter"])
    sub_task = SubTask(
        id="st-1", task_type=TaskType.DRAFTING, assigned_role=AgentRole.DRAFTER, description="d"
    )

    agent_id = engine.assign_agent("m1", sub_task, team)

    assert agent_id == "agent-drafter"
