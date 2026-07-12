from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.business_platform.bootstrap import get_business_quota_engine, get_metering_engine
from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.schemas import MeteredDimension
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission
from tmis.workflow_automation.action_engine.schemas import Action, new_action_id
from tmis.workflow_automation.api.schemas import (
    ApprovalConfigureRequest,
    ApprovalDecideRequest,
    ApprovalRequestRequest,
    ApprovalRequestResponse,
    AuditEntryResponse,
    ExecutionResponse,
    ExecutionResumeRequest,
    ExecutionStartRequest,
    RuleCreateRequest,
    RuleEvaluateRequest,
    RuleResponse,
    SimulatedStepOutcomeResponse,
    SimulateRequest,
    SimulationReportResponse,
    StepExecutionResultResponse,
    TemplateInstantiateRequest,
    TemplateResponse,
    WorkflowActionRequest,
    WorkflowCreateRequest,
    WorkflowResponse,
    WorkflowVersionRequest,
)
from tmis.workflow_automation.approval_gateway.engine import ApprovalGatewayEngine
from tmis.workflow_automation.audit.engine import WorkflowAuditEngine
from tmis.workflow_automation.bootstrap import (
    get_approval_gateway_engine,
    get_execution_engine,
    get_rule_engine,
    get_simulation_engine,
    get_template_library,
    get_workflow_audit_engine,
    get_workflow_engine,
)
from tmis.workflow_automation.condition_engine.schemas import Comparator, cond_compare
from tmis.workflow_automation.execution_engine.engine import ExecutionEngine
from tmis.workflow_automation.execution_engine.schemas import StepExecutionResult
from tmis.workflow_automation.rule_engine.engine import RuleEngine
from tmis.workflow_automation.simulation.engine import SimulationEngine
from tmis.workflow_automation.template_library.engine import TemplateLibrary
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType, new_trigger_id
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine
from tmis.workflow_automation.workflow_engine.schemas import Workflow, WorkflowStep

router = APIRouter(prefix="/workflow-automation", tags=["workflow-automation"])


def _workflow_response(workflow: Workflow) -> WorkflowResponse:
    return WorkflowResponse(
        id=workflow.id,
        workflow_key=workflow.workflow_key,
        firm_id=workflow.firm_id,
        name=workflow.name,
        version=workflow.version,
        owner=workflow.owner,
        description=workflow.description,
        status=workflow.status.value,
        step_count=len(workflow.steps),
        trigger_count=len(workflow.triggers),
    )


@router.post("/workflows", response_model=WorkflowResponse)
def create_workflow(
    payload: WorkflowCreateRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    triggers = tuple(
        Trigger(
            id=new_trigger_id(),
            workflow_id="",
            trigger_type=TriggerType(t.trigger_type),
            config=t.config,
        )
        for t in payload.triggers
    )
    steps = tuple(
        WorkflowStep(
            order=s.order,
            name=s.name,
            action=Action(
                id=new_action_id(),
                workflow_id="",
                action_type=s.action_type,
                config=s.action_config,
            ),
            parallel_group=s.parallel_group,
        )
        for s in payload.steps
    )
    workflow = engine.create(
        payload.firm_id,
        payload.name,
        payload.owner,
        description=payload.description,
        triggers=triggers,
        steps=steps,
    )
    return _workflow_response(workflow)


@router.post("/workflows/{workflow_id}/versions", response_model=WorkflowResponse)
def new_workflow_version(
    workflow_id: str,
    payload: WorkflowVersionRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    try:
        current = engine.get(payload.firm_id, workflow_id)
        steps = None
        if payload.steps is not None:
            steps = tuple(
                WorkflowStep(
                    order=s.order,
                    name=s.name,
                    action=Action(
                        id=new_action_id(),
                        workflow_id="",
                        action_type=s.action_type,
                        config=s.action_config,
                    ),
                    parallel_group=s.parallel_group,
                )
                for s in payload.steps
            )
        new_version = engine.new_version(
            payload.firm_id,
            current.workflow_key,
            payload.owner,
            description=payload.description,
            steps=steps,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _workflow_response(new_version)


@router.post("/workflows/{workflow_id}/activate", response_model=WorkflowResponse)
def activate_workflow(
    workflow_id: str,
    payload: WorkflowActionRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    try:
        workflow = engine.activate(payload.firm_id, workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _workflow_response(workflow)


@router.post("/workflows/{workflow_id}/archive", response_model=WorkflowResponse)
def archive_workflow(
    workflow_id: str,
    payload: WorkflowActionRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    try:
        workflow = engine.archive(payload.firm_id, workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _workflow_response(workflow)


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    firm_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    try:
        workflow = engine.get(firm_id, workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _workflow_response(workflow)


@router.get("/workflows/key/{workflow_key}/versions", response_model=list[WorkflowResponse])
def list_workflow_versions(
    workflow_key: str,
    firm_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine),
) -> list[WorkflowResponse]:
    return [_workflow_response(w) for w in engine.list_versions(firm_id, workflow_key)]


@router.get("/templates", response_model=list[TemplateResponse])
def list_templates(
    case_type: str | None = None,
    library: TemplateLibrary = Depends(get_template_library),
) -> list[TemplateResponse]:
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            case_type=t.case_type,
            description=t.description,
            customizable=t.customizable,
        )
        for t in library.list_templates(case_type)
    ]


@router.post("/templates/{template_id}/instantiate", response_model=WorkflowResponse)
def instantiate_template(
    template_id: str,
    payload: TemplateInstantiateRequest,
    library: TemplateLibrary = Depends(get_template_library),
) -> WorkflowResponse:
    try:
        workflow = library.instantiate(
            template_id, payload.firm_id, payload.owner, payload.overrides
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _workflow_response(workflow)


@router.post("/rules", response_model=RuleResponse)
def create_rule(
    payload: RuleCreateRequest,
    engine: RuleEngine = Depends(get_rule_engine),
) -> RuleResponse:
    try:
        comparator = Comparator(payload.comparator)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    condition = cond_compare(payload.field, comparator, payload.value)
    rule = engine.create_rule(payload.firm_id, payload.name, condition, payload.description)
    return RuleResponse(
        id=rule.id,
        firm_id=rule.firm_id,
        name=rule.name,
        description=rule.description,
        active=rule.active,
    )


@router.get("/rules", response_model=list[RuleResponse])
def list_rules(
    firm_id: str,
    active_only: bool = False,
    engine: RuleEngine = Depends(get_rule_engine),
) -> list[RuleResponse]:
    return [
        RuleResponse(
            id=r.id, firm_id=r.firm_id, name=r.name, description=r.description, active=r.active
        )
        for r in engine.list_rules(firm_id, active_only)
    ]


@router.post("/rules/{rule_id}/deactivate", response_model=RuleResponse)
def deactivate_rule(
    rule_id: str,
    firm_id: str,
    engine: RuleEngine = Depends(get_rule_engine),
) -> RuleResponse:
    try:
        rule = engine.deactivate_rule(firm_id, rule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RuleResponse(
        id=rule.id,
        firm_id=rule.firm_id,
        name=rule.name,
        description=rule.description,
        active=rule.active,
    )


@router.post("/rules/{rule_id}/evaluate", response_model=bool)
def evaluate_rule(
    rule_id: str,
    payload: RuleEvaluateRequest,
    engine: RuleEngine = Depends(get_rule_engine),
) -> bool:
    try:
        return engine.evaluate(payload.firm_id, rule_id, payload.context)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _step_result_response(result: StepExecutionResult) -> StepExecutionResultResponse:
    return StepExecutionResultResponse(
        step_order=result.step_order,
        skipped=result.skipped,
        success=result.action_result.success if result.action_result else None,
        detail=result.action_result.detail if result.action_result else None,
    )


@router.post("/executions/start", response_model=ExecutionResponse)
async def start_execution(
    payload: ExecutionStartRequest,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    execution_engine: ExecutionEngine = Depends(get_execution_engine),
    business_quotas: BusinessQuotaEngine = Depends(get_business_quota_engine),
    metering: MeteringEngine = Depends(get_metering_engine),
) -> ExecutionResponse:
    try:
        workflow = workflow_engine.get(payload.firm_id, payload.workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        used = metering.total_for_dimension(payload.firm_id, MeteredDimension.WORKFLOWS_EXECUTED)
        result = business_quotas.check(payload.firm_id, QuotaDimension.WORKFLOWS, int(used))
        if not result.allowed:
            raise HTTPException(
                status_code=429, detail="workflow execution quota exceeded for this firm's plan"
            )
    except KeyError:
        pass  # firm has no business_platform subscription yet — not gated
    execution = await execution_engine.start(workflow, payload.context)
    metering.record(payload.firm_id, MeteredDimension.WORKFLOWS_EXECUTED, 1)
    return ExecutionResponse(
        id=execution.id,
        firm_id=execution.firm_id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        current_step_index=execution.current_step_index,
        failure_reason=execution.failure_reason,
        step_results=[_step_result_response(r) for r in execution.step_results],
    )


@router.post("/executions/{execution_id}/resume", response_model=ExecutionResponse)
async def resume_execution(
    execution_id: str,
    payload: ExecutionResumeRequest,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    execution_engine: ExecutionEngine = Depends(get_execution_engine),
) -> ExecutionResponse:
    try:
        execution = execution_engine.get(payload.firm_id, execution_id)
        workflow = workflow_engine.get(payload.firm_id, payload.workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    execution = await execution_engine.resume(execution, workflow, payload.context)
    return ExecutionResponse(
        id=execution.id,
        firm_id=execution.firm_id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        current_step_index=execution.current_step_index,
        failure_reason=execution.failure_reason,
        step_results=[_step_result_response(r) for r in execution.step_results],
    )


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str,
    firm_id: str,
    execution_engine: ExecutionEngine = Depends(get_execution_engine),
) -> ExecutionResponse:
    try:
        execution = execution_engine.get(firm_id, execution_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExecutionResponse(
        id=execution.id,
        firm_id=execution.firm_id,
        workflow_id=execution.workflow_id,
        status=execution.status.value,
        current_step_index=execution.current_step_index,
        failure_reason=execution.failure_reason,
        step_results=[_step_result_response(r) for r in execution.step_results],
    )


@router.post("/simulate", response_model=SimulationReportResponse)
def simulate_workflow(
    payload: SimulateRequest,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    simulation_engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationReportResponse:
    try:
        workflow = workflow_engine.get(payload.firm_id, payload.workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    report = simulation_engine.simulate(workflow, payload.context)
    return SimulationReportResponse(
        workflow_id=report.workflow_id,
        would_complete=report.would_complete,
        workflow_condition_failure=report.workflow_condition_failure,
        steps=[
            SimulatedStepOutcomeResponse(
                step_order=s.step_order,
                name=s.name,
                would_run=s.would_run,
                skip_reason=s.skip_reason,
            )
            for s in report.steps
        ],
    )


@router.post("/approvals/configure")
def configure_approval(
    payload: ApprovalConfigureRequest,
    engine: ApprovalGatewayEngine = Depends(get_approval_gateway_engine),
) -> dict[str, bool]:
    engine.configure(payload.firm_id, payload.action_type, payload.required)
    return {"configured": True}


@router.get("/approvals/requires")
def approval_required(
    firm_id: str,
    action_type: str,
    engine: ApprovalGatewayEngine = Depends(get_approval_gateway_engine),
) -> dict[str, bool]:
    return {"required": engine.requires_approval(firm_id, action_type)}


@router.post("/approvals/request", response_model=ApprovalRequestResponse)
def request_approval(
    payload: ApprovalRequestRequest,
    engine: ApprovalGatewayEngine = Depends(get_approval_gateway_engine),
) -> ApprovalRequestResponse:
    request = engine.request_approval(
        payload.firm_id, payload.action_id, payload.requested_by, payload.approver_ids
    )
    return ApprovalRequestResponse(
        id=request.id, production_id=request.production_id, status=request.status.value
    )


@router.post("/approvals/{request_id}/decide", response_model=ApprovalRequestResponse)
def decide_approval(
    request_id: str,
    payload: ApprovalDecideRequest,
    engine: ApprovalGatewayEngine = Depends(get_approval_gateway_engine),
) -> ApprovalRequestResponse:
    try:
        decision = ValidationDecisionType(payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    authorize_or_403(payload.firm_id, payload.approver_id, Permission.CONSULTATION_VALIDATE)
    try:
        request = engine.decide(
            payload.firm_id, request_id, payload.approver_id, decision, payload.comment
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApprovalRequestResponse(
        id=request.id, production_id=request.production_id, status=request.status.value
    )


@router.get("/audit", response_model=list[AuditEntryResponse])
def list_audit(
    firm_id: str,
    engine: WorkflowAuditEngine = Depends(get_workflow_audit_engine),
) -> list[AuditEntryResponse]:
    return [
        AuditEntryResponse(
            id=e.id,
            workflow_id=e.workflow_id,
            execution_id=e.execution_id,
            actor_id=e.actor_id,
            action=e.action,
            detail=e.detail,
        )
        for e in engine.list_for_firm(firm_id)
    ]


@router.get("/audit/export", response_class=PlainTextResponse)
def export_audit(
    firm_id: str,
    engine: WorkflowAuditEngine = Depends(get_workflow_audit_engine),
) -> str:
    return engine.export_csv(firm_id)
