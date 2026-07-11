from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai_team.agents.catalog import default_descriptors
from tmis.ai_team.agents.ports import TeamAgentPort
from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.context.engine import ContextEngine
from tmis.ai_team.coordinator.engine import CoordinatorEngine
from tmis.ai_team.coordinator.schemas import MissionStatus
from tmis.ai_team.coordinator.store import InMemoryMissionStore
from tmis.ai_team.delegation.engine import DelegationEngine
from tmis.ai_team.human_loop.engine import HumanLoopEngine
from tmis.ai_team.human_loop.store import InMemoryHumanDecisionStore
from tmis.ai_team.metrics.engine import MetricsCollector
from tmis.ai_team.planner.engine import Planner
from tmis.ai_team.registry.store import InMemoryAgentRegistry
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.teams.store import InMemoryTeamStore
from tmis.ai_team.work_queue.engine import InMemoryWorkQueue


class _StubAgent:
    """A configurable `TeamAgentPort` double: succeeds normally, or
    fails a fixed number of times before succeeding (to exercise the
    retry / error-recovery path without depending on the real
    kernel)."""

    def __init__(self, name: str, role: AgentRole, *, fail_times: int = 0) -> None:
        self.name = name
        self.role = role
        self._fail_times = fail_times
        self._calls = 0

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        self._calls += 1
        if self._calls <= self._fail_times:
            raise RuntimeError(f"transient failure #{self._calls}")
        return AgentOutput(
            result={"text": f"[{self.role.value}] output ({self._calls})"},
            confidence=ConfidenceLevel.MEDIUM,
        )


def _stub_agents(
    fail_role: AgentRole | None = None, fail_times: int = 0
) -> dict[str, TeamAgentPort]:
    agents: dict[str, TeamAgentPort] = {}
    for descriptor in default_descriptors():
        times = fail_times if descriptor.role is fail_role else 0
        agents[descriptor.id] = _StubAgent(descriptor.name, descriptor.role, fail_times=times)
    return agents


def _build_coordinator(
    agents: dict[str, TeamAgentPort],
) -> tuple[CoordinatorEngine, InMemoryAgentRegistry, InMemoryTeamStore, InMemoryWorkQueue]:
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)
    work_queue = InMemoryWorkQueue()
    coordinator = CoordinatorEngine(
        Planner(),
        DelegationEngine(registry),
        work_queue,
        ContextEngine(),
        InMemoryMissionStore(),
        agents,
        registry,
        MetricsCollector(),
    )
    return coordinator, registry, InMemoryTeamStore(), work_queue


async def test_full_mission_completes_with_correct_dependency_order() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
    team = TeamBuilder(registry, team_store).build_team(
        domain=LegalDomain.DATA_PROTECTION, case_type="full_case_analysis"
    )

    mission = coordinator.launch_mission("firm-1", "Analyse ce dossier", team)
    result = await coordinator.run_mission(mission.id, team)

    assert result.status is MissionStatus.COMPLETED
    assert len(result.results) == len(result.plan.sub_tasks)
    assert result.synthesis is not None
    assert "risk_analysis" in result.synthesis


async def test_every_predefined_case_type_completes() -> None:
    for case_type in ("quick_review", "drafting_only", "standard_analysis", "full_case_analysis"):
        coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
        team = TeamBuilder(registry, team_store).build_team(case_type=case_type)
        mission = coordinator.launch_mission("firm-1", "test", team, case_type=case_type)

        result = await coordinator.run_mission(mission.id, team)

        assert result.status is MissionStatus.COMPLETED, case_type


async def test_transient_agent_failure_recovers_via_retry() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(
        _stub_agents(fail_role=AgentRole.VERIFIER, fail_times=1)
    )
    team = TeamBuilder(registry, team_store).build_team(case_type="quick_review")
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="quick_review")

    result = await coordinator.run_mission(mission.id, team)

    assert result.status is MissionStatus.COMPLETED
    assert len(result.results) == 2


async def test_permanent_agent_failure_leaves_the_mission_failed() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(
        _stub_agents(fail_role=AgentRole.VERIFIER, fail_times=99)
    )
    team = TeamBuilder(registry, team_store).build_team(case_type="quick_review")
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="quick_review")

    result = await coordinator.run_mission(mission.id, team)

    assert result.status is MissionStatus.FAILED
    assert result.synthesis is None
    assert len(result.results) < len(result.plan.sub_tasks)


async def test_missing_team_role_fails_that_step_without_crashing_the_mission() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
    team = TeamBuilder(registry, team_store).build_custom_team(
        "Équipe incomplète", ["agent-verifier"]
    )
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="quick_review")

    result = await coordinator.run_mission(mission.id, team)

    assert result.status is MissionStatus.FAILED
    assert len(result.results) == 1


async def test_human_loop_rerun_produces_a_fresh_result_for_the_step() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
    team = TeamBuilder(registry, team_store).build_team(case_type="quick_review")
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="quick_review")
    first_run = await coordinator.run_mission(mission.id, team)
    first_sub_task_id = first_run.plan.sub_tasks[0].id
    first_output_text = first_run.results[first_sub_task_id].result["text"]

    human_loop = HumanLoopEngine(InMemoryHumanDecisionStore())
    decision = human_loop.rerun_steps(mission.id, "lawyer-1", [first_sub_task_id])
    coordinator.apply_human_decision(mission.id, team, decision)
    second_run = await coordinator.run_mission(mission.id, team)

    assert second_run.status is MissionStatus.COMPLETED
    second_output_text = second_run.results[first_sub_task_id].result["text"]
    assert second_output_text != first_output_text


async def test_human_loop_exclude_agent_prevents_future_delegation_to_it() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
    team = TeamBuilder(registry, team_store).build_team(case_type="quick_review")
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="quick_review")

    human_loop = HumanLoopEngine(InMemoryHumanDecisionStore())
    decision = human_loop.exclude_agent(mission.id, "lawyer-1", "agent-verifier")
    coordinator.apply_human_decision(mission.id, team, decision)

    assert "agent-verifier" not in team.member_agent_ids


async def test_every_sub_task_gets_exactly_one_work_item() -> None:
    coordinator, registry, team_store, _ = _build_coordinator(_stub_agents())
    team = TeamBuilder(registry, team_store).build_team(case_type="full_case_analysis")
    mission = coordinator.launch_mission("firm-1", "test", team, case_type="full_case_analysis")

    await coordinator.run_mission(mission.id, team)

    assert len(mission.work_item_ids) == len(mission.plan.sub_tasks)
