from pydantic import BaseModel, Field

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.teams.schemas import MissionComplexity


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    skills: list[str]
    tools: list[str]
    compatible_models: list[str]
    estimated_cost_usd: float
    average_duration_seconds: float
    quality_score: float
    version: str


class TeamCreateRequest(BaseModel):
    domain: LegalDomain = LegalDomain.GENERAL
    complexity: MissionComplexity = MissionComplexity.MEDIUM
    case_type: str = "full_case_analysis"
    target_cost_usd: float | None = None
    desired_delay_seconds: float | None = None


class CustomTeamCreateRequest(BaseModel):
    name: str
    agent_ids: list[str]


class TeamResponse(BaseModel):
    id: str
    name: str
    member_agent_ids: list[str]
    domain: str
    is_custom: bool


class MissionCreateRequest(BaseModel):
    firm_id: str
    request_description: str
    team_id: str
    case_type: str = "full_case_analysis"
    requested_by: str | None = None


class SubTaskResponse(BaseModel):
    id: str
    task_type: str
    assigned_role: str
    description: str
    depends_on: list[str]


class MissionResponse(BaseModel):
    id: str
    firm_id: str
    request_description: str
    domain: str
    team_id: str
    status: str
    plan: list[SubTaskResponse]
    completed_sub_tasks: int
    total_sub_tasks: int


class SubTaskResultResponse(BaseModel):
    sub_task_id: str
    task_type: str
    text: str
    confidence: str
    warnings: list[str]


class MissionResultsResponse(BaseModel):
    mission_id: str
    status: str
    synthesis: str | None
    results: list[SubTaskResultResponse]


class MissionMetricsResponse(BaseModel):
    mission_id: str
    total_cost_usd: float
    total_duration_seconds: float
    agent_runs: int
    consensus_rate: float
    revision_count: int
    human_validation_count: int


class SupervisionDashboardResponse(BaseModel):
    """The AI Team Platform's supervision dashboard (see
    docs/55-guide-coordinateur.md — Observabilité): a curated
    cross-mission snapshot, distinct from `/platform/metrics`
    (Sprint 10) which is the exhaustive Prometheus feed the same
    counters/histograms recorded here also flow into."""

    total_missions: int
    missions_by_status: dict[str, int]
    total_agent_runs: int
    total_cost_usd: float
    pending_work_items: int
    running_work_items: int
    failed_work_items: int


class HumanDecisionRequest(BaseModel):
    actor_id: str
    decision_type: str = Field(
        description=(
            "One of: approve, request_new_analysis, exclude_agent, "
            "add_agent, modify_plan, rerun_steps"
        )
    )
    sub_task_id: str | None = None
    sub_task_ids: list[str] | None = None
    agent_id: str | None = None
    note: str | None = None


class HumanDecisionResponse(BaseModel):
    id: str
    mission_id: str
    actor_id: str
    decision_type: str
    payload: dict[str, str]
