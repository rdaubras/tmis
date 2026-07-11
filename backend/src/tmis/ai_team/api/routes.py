from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_team.api.schemas import (
    AgentResponse,
    CustomTeamCreateRequest,
    HumanDecisionRequest,
    HumanDecisionResponse,
    MissionCreateRequest,
    MissionMetricsResponse,
    MissionResponse,
    MissionResultsResponse,
    SubTaskResponse,
    SubTaskResultResponse,
    SupervisionDashboardResponse,
    TeamCreateRequest,
    TeamResponse,
)
from tmis.ai_team.bootstrap import (
    get_coordinator_engine,
    get_human_loop_engine,
    get_metrics_collector,
    get_mission_store,
    get_team_builder,
    get_team_store,
    get_work_queue,
)
from tmis.ai_team.coordinator.engine import CoordinatorEngine
from tmis.ai_team.coordinator.schemas import Mission
from tmis.ai_team.coordinator.store import InMemoryMissionStore
from tmis.ai_team.human_loop.engine import HumanLoopEngine
from tmis.ai_team.human_loop.schemas import HumanDecisionType
from tmis.ai_team.metrics.engine import MetricsCollector
from tmis.ai_team.registry.bootstrap import get_agent_registry
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.teams.schemas import Team
from tmis.ai_team.teams.store import InMemoryTeamStore
from tmis.ai_team.work_queue.engine import InMemoryWorkQueue
from tmis.ai_team.work_queue.schemas import WorkItemStatus

router = APIRouter(prefix="/ai-team", tags=["ai-team"])


def _get_team_or_404(team_id: str, store: InMemoryTeamStore) -> Team:
    team = store.get(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"team {team_id} not found")
    return team


def _get_mission_or_404(mission_id: str, mission_store: InMemoryMissionStore) -> Mission:
    mission = mission_store.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail=f"mission {mission_id} not found")
    return mission


def _to_mission_response(mission: Mission) -> MissionResponse:
    return MissionResponse(
        id=mission.id,
        firm_id=mission.firm_id,
        request_description=mission.request_description,
        domain=mission.domain.value,
        team_id=mission.team_id,
        status=mission.status.value,
        plan=[
            SubTaskResponse(
                id=st.id,
                task_type=st.task_type.value,
                assigned_role=st.assigned_role.value,
                description=st.description,
                depends_on=list(st.depends_on),
            )
            for st in mission.plan.sub_tasks
        ],
        completed_sub_tasks=len(mission.results),
        total_sub_tasks=len(mission.plan.sub_tasks),
    )


@router.get("/agents", response_model=list[AgentResponse])
def list_agents() -> list[AgentResponse]:
    return [
        AgentResponse(
            id=d.id,
            name=d.name,
            role=d.role.value,
            description=d.description,
            skills=sorted(d.skills),
            tools=sorted(d.tools),
            compatible_models=sorted(d.compatible_models),
            estimated_cost_usd=d.estimated_cost_usd,
            average_duration_seconds=d.average_duration_seconds,
            quality_score=d.quality_score,
            version=d.version,
        )
        for d in get_agent_registry().list_all()
    ]


@router.post("/teams", response_model=TeamResponse)
def create_team(
    request: TeamCreateRequest, builder: TeamBuilder = Depends(get_team_builder)
) -> TeamResponse:
    team = builder.build_team(
        domain=request.domain,
        complexity=request.complexity,
        case_type=request.case_type,
        target_cost_usd=request.target_cost_usd,
        desired_delay_seconds=request.desired_delay_seconds,
    )
    return TeamResponse(
        id=team.id,
        name=team.name,
        member_agent_ids=team.member_agent_ids,
        domain=team.domain.value,
        is_custom=team.is_custom,
    )


@router.post("/teams/custom", response_model=TeamResponse)
def create_custom_team(
    request: CustomTeamCreateRequest, builder: TeamBuilder = Depends(get_team_builder)
) -> TeamResponse:
    team = builder.build_custom_team(request.name, request.agent_ids)
    return TeamResponse(
        id=team.id,
        name=team.name,
        member_agent_ids=team.member_agent_ids,
        domain=team.domain.value,
        is_custom=team.is_custom,
    )


@router.post("/missions", response_model=MissionResponse)
def launch_mission(
    request: MissionCreateRequest,
    coordinator: CoordinatorEngine = Depends(get_coordinator_engine),
    team_store: InMemoryTeamStore = Depends(get_team_store),
) -> MissionResponse:
    team = _get_team_or_404(request.team_id, team_store)
    mission = coordinator.launch_mission(
        request.firm_id, request.request_description, team, case_type=request.case_type
    )
    return _to_mission_response(mission)


@router.post("/missions/{mission_id}/run", response_model=MissionResponse)
async def run_mission(
    mission_id: str,
    coordinator: CoordinatorEngine = Depends(get_coordinator_engine),
    mission_store: InMemoryMissionStore = Depends(get_mission_store),
    team_store: InMemoryTeamStore = Depends(get_team_store),
) -> MissionResponse:
    mission = _get_mission_or_404(mission_id, mission_store)
    team = _get_team_or_404(mission.team_id, team_store)
    result = await coordinator.run_mission(mission_id, team)
    return _to_mission_response(result)


@router.get("/missions/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str, mission_store: InMemoryMissionStore = Depends(get_mission_store)
) -> MissionResponse:
    return _to_mission_response(_get_mission_or_404(mission_id, mission_store))


@router.get("/missions/{mission_id}/results", response_model=MissionResultsResponse)
def get_mission_results(
    mission_id: str, mission_store: InMemoryMissionStore = Depends(get_mission_store)
) -> MissionResultsResponse:
    mission = _get_mission_or_404(mission_id, mission_store)
    sub_tasks_by_id = {st.id: st for st in mission.plan.sub_tasks}
    return MissionResultsResponse(
        mission_id=mission.id,
        status=mission.status.value,
        synthesis=mission.synthesis,
        results=[
            SubTaskResultResponse(
                sub_task_id=sub_task_id,
                task_type=sub_tasks_by_id[sub_task_id].task_type.value,
                text=str(output.result.get("text", "")),
                confidence=output.confidence.value,
                warnings=list(output.warnings),
            )
            for sub_task_id, output in mission.results.items()
        ],
    )


@router.get("/dashboard", response_model=SupervisionDashboardResponse)
def get_dashboard(
    mission_store: InMemoryMissionStore = Depends(get_mission_store),
    metrics: MetricsCollector = Depends(get_metrics_collector),
    work_queue: InMemoryWorkQueue = Depends(get_work_queue),
) -> SupervisionDashboardResponse:
    missions = mission_store.list_all()
    missions_by_status: dict[str, int] = {}
    for mission in missions:
        status = mission.status.value
        missions_by_status[status] = missions_by_status.get(status, 0) + 1

    work_items = work_queue.list_all()
    return SupervisionDashboardResponse(
        total_missions=len(missions),
        missions_by_status=missions_by_status,
        total_agent_runs=len(metrics.all_agent_runs()),
        total_cost_usd=sum(r.cost_usd for r in metrics.all_agent_runs()),
        pending_work_items=sum(1 for i in work_items if i.status is WorkItemStatus.PENDING),
        running_work_items=sum(1 for i in work_items if i.status is WorkItemStatus.RUNNING),
        failed_work_items=sum(1 for i in work_items if i.status is WorkItemStatus.FAILED),
    )


@router.get("/missions/{mission_id}/metrics", response_model=MissionMetricsResponse)
def get_mission_metrics(
    mission_id: str,
    mission_store: InMemoryMissionStore = Depends(get_mission_store),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> MissionMetricsResponse:
    _get_mission_or_404(mission_id, mission_store)
    summary = metrics.summary_for_mission(mission_id)
    return MissionMetricsResponse(
        mission_id=summary.mission_id,
        total_cost_usd=summary.total_cost_usd,
        total_duration_seconds=summary.total_duration_seconds,
        agent_runs=summary.agent_runs,
        consensus_rate=summary.consensus_rate,
        revision_count=summary.revision_count,
        human_validation_count=summary.human_validation_count,
    )


@router.post("/missions/{mission_id}/human-decisions", response_model=HumanDecisionResponse)
def record_human_decision(
    mission_id: str,
    request: HumanDecisionRequest,
    coordinator: CoordinatorEngine = Depends(get_coordinator_engine),
    human_loop: HumanLoopEngine = Depends(get_human_loop_engine),
    mission_store: InMemoryMissionStore = Depends(get_mission_store),
    team_store: InMemoryTeamStore = Depends(get_team_store),
) -> HumanDecisionResponse:
    mission = _get_mission_or_404(mission_id, mission_store)
    team = _get_team_or_404(mission.team_id, team_store)

    try:
        decision_type = HumanDecisionType(request.decision_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"unknown decision_type {request.decision_type!r}"
        ) from exc

    if decision_type is HumanDecisionType.APPROVE:
        decision = human_loop.approve(mission_id, request.actor_id)
    elif decision_type is HumanDecisionType.REQUEST_NEW_ANALYSIS:
        if not request.sub_task_id:
            raise HTTPException(status_code=400, detail="sub_task_id is required")
        decision = human_loop.request_new_analysis(
            mission_id, request.actor_id, request.sub_task_id
        )
    elif decision_type is HumanDecisionType.EXCLUDE_AGENT:
        if not request.agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
        decision = human_loop.exclude_agent(mission_id, request.actor_id, request.agent_id)
    elif decision_type is HumanDecisionType.ADD_AGENT:
        if not request.agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
        decision = human_loop.add_agent(mission_id, request.actor_id, request.agent_id)
    elif decision_type is HumanDecisionType.MODIFY_PLAN:
        decision = human_loop.modify_plan(mission_id, request.actor_id, request.note or "")
    else:
        if not request.sub_task_ids:
            raise HTTPException(status_code=400, detail="sub_task_ids is required")
        decision = human_loop.rerun_steps(mission_id, request.actor_id, request.sub_task_ids)

    coordinator.apply_human_decision(mission_id, team, decision)

    return HumanDecisionResponse(
        id=decision.id,
        mission_id=decision.mission_id,
        actor_id=decision.actor_id,
        decision_type=decision.decision_type.value,
        payload=decision.payload,
    )
