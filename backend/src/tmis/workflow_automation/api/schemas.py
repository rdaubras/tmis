from pydantic import BaseModel


class TriggerPayload(BaseModel):
    trigger_type: str
    config: dict[str, str] = {}


class WorkflowStepPayload(BaseModel):
    order: int
    name: str
    action_type: str
    action_config: dict[str, str] = {}
    parallel_group: str | None = None


class WorkflowCreateRequest(BaseModel):
    firm_id: str
    name: str
    owner: str
    description: str = ""
    triggers: list[TriggerPayload] = []
    steps: list[WorkflowStepPayload] = []


class WorkflowVersionRequest(BaseModel):
    firm_id: str
    owner: str
    description: str | None = None
    steps: list[WorkflowStepPayload] | None = None


class WorkflowActionRequest(BaseModel):
    firm_id: str


class WorkflowResponse(BaseModel):
    id: str
    workflow_key: str
    firm_id: str
    name: str
    version: int
    owner: str
    description: str
    status: str
    step_count: int
    trigger_count: int


class TemplateResponse(BaseModel):
    id: str
    name: str
    case_type: str
    description: str
    customizable: bool


class TemplateInstantiateRequest(BaseModel):
    firm_id: str
    owner: str
    overrides: dict[int, dict[str, str]] | None = None


class RuleCreateRequest(BaseModel):
    firm_id: str
    name: str
    description: str = ""
    field: str
    comparator: str
    value: str


class RuleResponse(BaseModel):
    id: str
    firm_id: str
    name: str
    description: str
    active: bool


class RuleEvaluateRequest(BaseModel):
    firm_id: str
    context: dict[str, str]


class ExecutionStartRequest(BaseModel):
    firm_id: str
    workflow_id: str
    context: dict[str, str] = {}


class ExecutionResumeRequest(BaseModel):
    firm_id: str
    workflow_id: str
    context: dict[str, str] = {}


class StepExecutionResultResponse(BaseModel):
    step_order: int
    skipped: bool
    success: bool | None
    detail: str | None


class ExecutionResponse(BaseModel):
    id: str
    firm_id: str
    workflow_id: str
    status: str
    current_step_index: int
    failure_reason: str | None
    step_results: list[StepExecutionResultResponse]


class SimulateRequest(BaseModel):
    firm_id: str
    workflow_id: str
    context: dict[str, str] = {}


class SimulatedStepOutcomeResponse(BaseModel):
    step_order: int
    name: str
    would_run: bool
    skip_reason: str | None


class SimulationReportResponse(BaseModel):
    workflow_id: str
    would_complete: bool
    workflow_condition_failure: str | None
    steps: list[SimulatedStepOutcomeResponse]


class ApprovalConfigureRequest(BaseModel):
    firm_id: str
    action_type: str
    required: bool


class ApprovalRequestRequest(BaseModel):
    firm_id: str
    action_id: str
    requested_by: str
    approver_ids: tuple[str, ...]


class ApprovalDecideRequest(BaseModel):
    firm_id: str
    approver_id: str
    decision: str
    comment: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: str
    production_id: str
    status: str


class AuditEntryResponse(BaseModel):
    id: str
    workflow_id: str
    execution_id: str | None
    actor_id: str
    action: str
    detail: str
