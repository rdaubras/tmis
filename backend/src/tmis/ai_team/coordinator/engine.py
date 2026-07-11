import time
import uuid
from datetime import UTC, datetime

import structlog

from tmis.ai.schemas.agent import AgentInput
from tmis.ai_team.agents.ports import TeamAgentPort
from tmis.ai_team.context.engine import ContextEngine
from tmis.ai_team.coordinator.ports import MissionStorePort
from tmis.ai_team.coordinator.schemas import Mission, MissionStatus
from tmis.ai_team.delegation.engine import DelegationEngine
from tmis.ai_team.human_loop.schemas import HumanDecision, HumanDecisionType
from tmis.ai_team.metrics.engine import MetricsCollector
from tmis.ai_team.planner.engine import Planner
from tmis.ai_team.planner.schemas import SubTask
from tmis.ai_team.registry.ports import AgentRegistryPort
from tmis.ai_team.teams.schemas import Team
from tmis.ai_team.work_queue.ports import WorkQueuePort
from tmis.ai_team.work_queue.schemas import WorkItem, WorkItemStatus
from tmis.platform.metrics.bootstrap import get_metrics_registry

_logger = structlog.get_logger(__name__)


class CoordinatorEngine:
    """The Coordinator (see docs/55-guide-coordinateur.md): splits a
    mission into sub-tasks (`Planner`), assigns each to an agent
    (`DelegationEngine`), tracks progress (`WorkQueuePort`), retries a
    failing agent automatically (the queue's own retry policy), and
    aggregates every result into a synthesis. **The Coordinator never
    performs an analysis itself** — `_build_synthesis` only concatenates
    what the agents produced, it never calls a model."""

    def __init__(
        self,
        planner: Planner,
        delegation: DelegationEngine,
        work_queue: WorkQueuePort,
        context_engine: ContextEngine,
        mission_store: MissionStorePort,
        agents: dict[str, TeamAgentPort],
        registry: AgentRegistryPort,
        metrics: MetricsCollector,
    ) -> None:
        self._planner = planner
        self._delegation = delegation
        self._work_queue = work_queue
        self._context_engine = context_engine
        self._missions = mission_store
        self._agents = agents
        self._registry = registry
        self._metrics = metrics

    def launch_mission(
        self,
        firm_id: str,
        request_description: str,
        team: Team,
        *,
        case_type: str = "full_case_analysis",
    ) -> Mission:
        plan = self._planner.decompose(team.domain, case_type=case_type)
        mission = Mission(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            request_description=request_description,
            domain=team.domain,
            team_id=team.id,
            plan=plan,
        )
        self._enqueue_ready_subtasks(mission, team)
        self._missions.save(mission)
        return mission

    def _enqueue_ready_subtasks(self, mission: Mission, team: Team) -> None:
        enqueued_sub_task_ids = {
            item.sub_task_id
            for item_id in mission.work_item_ids
            if (item := self._work_queue.get(item_id)) is not None
        }
        for sub_task in mission.plan.sub_tasks:
            ready = all(dep in mission.results for dep in sub_task.depends_on)
            if sub_task.id in enqueued_sub_task_ids or not ready:
                continue
            agent_id = self._delegation.assign_agent(mission.id, sub_task, team)
            work_item = WorkItem(
                id=str(uuid.uuid4()),
                sub_task_id=sub_task.id,
                agent_id=agent_id or "",
                priority=len(mission.plan.sub_tasks) - mission.plan.sub_tasks.index(sub_task),
            )
            self._work_queue.enqueue(work_item)
            mission.work_item_ids.append(work_item.id)
            _logger.info(
                "ai_team.delegation",
                mission_id=mission.id,
                sub_task_id=sub_task.id,
                task_type=sub_task.task_type.value,
                assigned_role=sub_task.assigned_role.value,
                agent_id=agent_id,
            )

    async def run_mission(self, mission_id: str, team: Team) -> Mission:
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError(f"mission {mission_id} not found")
        mission.status = MissionStatus.RUNNING
        mission_context: dict[str, object] = {"case_summary": mission.request_description}
        sub_tasks_by_id: dict[str, SubTask] = {st.id: st for st in mission.plan.sub_tasks}

        while True:
            item = self._next_runnable_item(mission)
            if item is None:
                break
            sub_task = sub_tasks_by_id[item.sub_task_id]
            self._work_queue.mark_running(item.id)

            agent = self._agents.get(item.agent_id) if item.agent_id else None
            if agent is None:
                role_name = sub_task.assigned_role.value
                self._work_queue.mark_failed(item.id, f"no agent available for {role_name}")
                _logger.warning(
                    "ai_team.agent_missing",
                    mission_id=mission.id,
                    sub_task_id=sub_task.id,
                    assigned_role=role_name,
                )
                continue

            context_slice = self._context_engine.build_context_for(
                mission.id, sub_task.assigned_role, mission_context
            )
            agent_input = AgentInput(
                task_id=uuid.uuid4(), case_id=None, context=context_slice.content
            )
            _logger.info(
                "ai_team.agent_started",
                mission_id=mission.id,
                sub_task_id=sub_task.id,
                agent_id=item.agent_id,
                attempt=item.attempts,
            )
            start = time.perf_counter()
            try:
                output = await agent.run(agent_input)
            except Exception as exc:  # noqa: BLE001 — a failing agent must never crash the mission
                failed_item = self._work_queue.mark_failed(item.id, str(exc))
                _logger.warning(
                    "ai_team.agent_failed",
                    mission_id=mission.id,
                    sub_task_id=sub_task.id,
                    agent_id=item.agent_id,
                    error=str(exc),
                    will_retry=failed_item.status is WorkItemStatus.RETRYING,
                )
                get_metrics_registry().counter(
                    "ai_team_agent_runs_total", "Total AI Team agent executions"
                ).inc(role=sub_task.assigned_role.value, status="failed")
                continue
            duration_seconds = time.perf_counter() - start

            self._work_queue.mark_done(item.id, output)
            mission.results[sub_task.id] = output
            mission_context[f"{sub_task.task_type.value}_result"] = output.result.get("text", "")
            descriptor = self._registry.get(item.agent_id)
            self._metrics.record_agent_run(
                mission.id,
                sub_task.id,
                item.agent_id,
                duration_seconds,
                descriptor.estimated_cost_usd if descriptor else 0.0,
                descriptor.quality_score if descriptor else 0.0,
            )
            _logger.info(
                "ai_team.agent_finished",
                mission_id=mission.id,
                sub_task_id=sub_task.id,
                agent_id=item.agent_id,
                duration_seconds=duration_seconds,
                confidence=output.confidence.value,
            )
            get_metrics_registry().counter(
                "ai_team_agent_runs_total", "Total AI Team agent executions"
            ).inc(role=sub_task.assigned_role.value, status="done")
            get_metrics_registry().histogram(
                "ai_team_agent_run_duration_seconds", "AI Team agent execution duration"
            ).observe(duration_seconds, role=sub_task.assigned_role.value)
            self._enqueue_ready_subtasks(mission, team)

        mission.completed_at = datetime.now(UTC)
        if len(mission.results) == len(mission.plan.sub_tasks):
            mission.synthesis = self._build_synthesis(mission)
            mission.status = MissionStatus.COMPLETED
        else:
            mission.status = MissionStatus.FAILED
        self._missions.save(mission)
        return mission

    def _next_runnable_item(self, mission: Mission) -> WorkItem | None:
        """Selects the highest-priority runnable item *belonging to
        this mission*. Deliberately does not delegate to
        `WorkQueuePort.dequeue_next()`, which scans the whole queue: a
        `WorkQueuePort` is typically shared by every concurrent
        mission, so a global dequeue could hand this mission another
        mission's work item."""
        candidates = [
            item
            for item_id in mission.work_item_ids
            if (item := self._work_queue.get(item_id)) is not None
            and item.status in (WorkItemStatus.PENDING, WorkItemStatus.RETRYING)
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item.priority, item.created_at))
        return candidates[0]

    def apply_human_decision(self, mission_id: str, team: Team, decision: HumanDecision) -> Mission:
        """Turns a recorded `HumanDecision` (see
        `tmis.ai_team.human_loop`) into an actual effect on the
        mission or team. `APPROVE` and `MODIFY_PLAN` carry no
        structural mutation this sprint — a free-form plan edit is a
        natural Sprint 12 extension; approval is itself the terminal,
        no-op-by-design decision."""
        mission = self._missions.get(mission_id)
        if mission is None:
            raise ValueError(f"mission {mission_id} not found")

        _logger.info(
            "ai_team.human_decision",
            mission_id=mission_id,
            actor_id=decision.actor_id,
            decision_type=decision.decision_type.value,
        )
        get_metrics_registry().counter(
            "ai_team_coordinator_decisions_total", "Total Coordinator/human decisions applied"
        ).inc(decision=decision.decision_type.value)
        self._metrics.record_human_validation(mission_id)
        if decision.decision_type is HumanDecisionType.EXCLUDE_AGENT:
            agent_id = decision.payload["agent_id"]
            team.member_agent_ids = [a for a in team.member_agent_ids if a != agent_id]
        elif decision.decision_type is HumanDecisionType.ADD_AGENT:
            agent_id = decision.payload["agent_id"]
            if agent_id not in team.member_agent_ids:
                team.member_agent_ids.append(agent_id)
        elif decision.decision_type in (
            HumanDecisionType.REQUEST_NEW_ANALYSIS,
            HumanDecisionType.RERUN_STEPS,
        ):
            self._metrics.record_revision(mission_id)
            self._rerun_sub_tasks(mission, team, self._sub_task_ids_from(decision))

        self._missions.save(mission)
        return mission

    @staticmethod
    def _sub_task_ids_from(decision: HumanDecision) -> list[str]:
        if decision.decision_type is HumanDecisionType.REQUEST_NEW_ANALYSIS:
            return [decision.payload["sub_task_id"]]
        return decision.payload["sub_task_ids"].split(",")

    def _rerun_sub_tasks(self, mission: Mission, team: Team, sub_task_ids: list[str]) -> None:
        sub_tasks_by_id = {st.id: st for st in mission.plan.sub_tasks}
        for sub_task_id in sub_task_ids:
            sub_task = sub_tasks_by_id.get(sub_task_id)
            if sub_task is None:
                continue
            mission.results.pop(sub_task_id, None)
            agent_id = self._delegation.assign_agent(mission.id, sub_task, team)
            work_item = WorkItem(
                id=str(uuid.uuid4()), sub_task_id=sub_task_id, agent_id=agent_id or ""
            )
            self._work_queue.enqueue(work_item)
            mission.work_item_ids.append(work_item.id)
        mission.status = MissionStatus.RUNNING

    def _build_synthesis(self, mission: Mission) -> str:
        """Purely structural aggregation — the Coordinator concatenates
        what each agent produced, it never generates new analysis."""
        sections = []
        for sub_task in mission.plan.sub_tasks:
            output = mission.results.get(sub_task.id)
            if output is None:
                continue
            text = output.result.get("text", "")
            sections.append(f"## {sub_task.task_type.value}\n{text}")
        return "\n\n".join(sections)
