from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_fabric.api.schemas import (
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    CompareRequest,
    ComparisonEntryResponse,
    ComparisonResultResponse,
    ConsensusOutcomeResponse,
    ConsensusRequest,
    CostSummaryResponse,
    CriticVerdictResponse,
    CritiqueRequest,
    ExecutionPlanResponse,
    FabricTelemetryResponse,
    FusedResponsePayload,
    FuseRequest,
    FusionSourceResponse,
    GovernanceEvaluateRequest,
    ModelDescriptorResponse,
    ModelTelemetrySnapshotResponse,
    PlannedStepResponse,
    PlanRequest,
    PolicyCreateRequest,
    PolicyDecisionResponse,
    PolicyResponse,
    ResponseMetricsPayload,
    RoutingDecisionResponse,
    RoutingRequestPayload,
)
from tmis.ai_fabric.benchmark.engine import BenchmarkEngine
from tmis.ai_fabric.benchmark.schemas import BenchmarkRun
from tmis.ai_fabric.bootstrap import (
    get_ai_intelligence_fabric,
    get_benchmark_engine,
    get_fabric_provider_registry,
    get_governance_engine,
    get_model_registry,
    get_policy_store,
    get_task_planner,
    get_telemetry_dashboard,
)
from tmis.ai_fabric.comparison.schemas import ComparisonResult
from tmis.ai_fabric.consensus.schemas import ConsensusOutcome, ModelPosition
from tmis.ai_fabric.critic.schemas import CriticVerdict
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.fusion.schemas import FusedResponse
from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.planner.engine import TaskPlanner
from tmis.ai_fabric.planner.schemas import ExecutionPlan
from tmis.ai_fabric.policies.ports import PolicyStorePort
from tmis.ai_fabric.policies.schemas import Policy, PolicyType, new_policy_id
from tmis.ai_fabric.provider_registry import FabricProviderRegistry
from tmis.ai_fabric.router.schemas import NoEligibleModelError, QuotaExceededError, RoutingRequest
from tmis.business_platform.bootstrap import get_business_quota_engine
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.platform.cost_control.bootstrap import get_cost_tracker_engine
from tmis.platform.cost_control.engine import CostTrackerEngine

router = APIRouter(prefix="/ai-fabric", tags=["ai-fabric"])


def _to_model_response(model: ModelDescriptor) -> ModelDescriptorResponse:
    return ModelDescriptorResponse(
        name=model.name,
        version=model.version,
        provider=model.provider,
        cost_per_1k_tokens_usd=model.cost_per_1k_tokens_usd,
        avg_latency_ms=model.avg_latency_ms,
        max_context_tokens=model.max_context_tokens,
        capabilities=sorted(c.value for c in model.capabilities),
        profiles=sorted(p.value for p in model.profiles),
        availability=model.availability,
        quality_score=model.quality_score,
        legal_score=model.legal_score,
        drafting_score=model.drafting_score,
        research_score=model.research_score,
        reasoning_score=model.reasoning_score,
    )


def _to_metrics_payload(metrics: object) -> ResponseMetricsPayload:
    return ResponseMetricsPayload(
        length_words=metrics.length_words,  # type: ignore[attr-defined]
        citation_count=metrics.citation_count,  # type: ignore[attr-defined]
        coherence_score=metrics.coherence_score,  # type: ignore[attr-defined]
        contradiction_flags=list(metrics.contradiction_flags),  # type: ignore[attr-defined]
    )


def _to_plan_response(plan: ExecutionPlan) -> ExecutionPlanResponse:
    steps = []
    for step in plan.steps:
        decision_response = (
            RoutingDecisionResponse(
                model=_to_model_response(step.decision.model),
                reasons=list(step.decision.reasons),
            )
            if step.decision is not None
            else None
        )
        steps.append(
            PlannedStepResponse(
                name=step.sub_task.name,
                kind=step.sub_task.kind.value,
                decision=decision_response,
            )
        )
    return ExecutionPlanResponse(task_description=plan.task_description, steps=steps)


def _to_policy_response(policy: Policy) -> PolicyResponse:
    return PolicyResponse(
        id=policy.id,
        type=policy.type.value,
        model_name=policy.model_name,
        reason=policy.reason,
        allowed_countries=(
            sorted(policy.allowed_countries) if policy.allowed_countries is not None else None
        ),
        allowed_data_types=(
            sorted(policy.allowed_data_types) if policy.allowed_data_types is not None else None
        ),
        active=policy.active,
    )


@router.get("/models", response_model=list[ModelDescriptorResponse])
def list_models(
    model_registry: ModelRegistryPort = Depends(get_model_registry),
) -> list[ModelDescriptorResponse]:
    return [_to_model_response(m) for m in model_registry.list_all()]


@router.get("/models/{model_name}", response_model=ModelDescriptorResponse)
def get_model(
    model_name: str, model_registry: ModelRegistryPort = Depends(get_model_registry)
) -> ModelDescriptorResponse:
    model = model_registry.get(model_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"model {model_name} not found")
    return _to_model_response(model)


@router.get("/providers", response_model=list[str])
def list_providers(
    providers: FabricProviderRegistry = Depends(get_fabric_provider_registry),
) -> list[str]:
    return providers.list_names()


@router.post("/route", response_model=RoutingDecisionResponse)
def route_request(
    payload: RoutingRequestPayload,
    fabric: AIIntelligenceFabric = Depends(get_ai_intelligence_fabric),
    business_quotas: BusinessQuotaEngine = Depends(get_business_quota_engine),
) -> RoutingDecisionResponse:
    try:
        if not business_quotas.check_ai_calls(payload.firm_id):
            raise HTTPException(
                status_code=429, detail="AI call quota exceeded for this firm's plan"
            )
    except KeyError:
        pass  # firm has no business_platform subscription yet — not gated
    request = RoutingRequest(
        firm_id=payload.firm_id,
        task_type=payload.task_type,
        prompt=payload.prompt,
        profile=ModelProfile(payload.profile) if payload.profile else None,
        target_cost_usd=payload.target_cost_usd,
        max_latency_ms=payload.max_latency_ms,
        min_quality_score=payload.min_quality_score,
        country=payload.country,
        data_type=payload.data_type,
    )
    try:
        decision = fabric.route(request)
    except NoEligibleModelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return RoutingDecisionResponse(
        model=_to_model_response(decision.model), reasons=list(decision.reasons)
    )


@router.post("/plan", response_model=ExecutionPlanResponse)
def plan_task(
    request: PlanRequest, planner: TaskPlanner = Depends(get_task_planner)
) -> ExecutionPlanResponse:
    try:
        plan = planner.plan(request.firm_id, request.task_description)
    except NoEligibleModelError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return _to_plan_response(plan)


@router.post("/compare", response_model=ComparisonResultResponse)
def compare_responses(
    request: CompareRequest, fabric: AIIntelligenceFabric = Depends(get_ai_intelligence_fabric)
) -> ComparisonResultResponse:
    result: ComparisonResult = fabric.compare(request.prompt, request.responses)
    return ComparisonResultResponse(
        prompt=result.prompt,
        entries=[
            ComparisonEntryResponse(
                model_name=e.model_name,
                metrics=_to_metrics_payload(e.metrics),
                coverage_score=e.coverage_score,
                prompt_compliance_score=e.prompt_compliance_score,
                overall_score=e.overall_score,
            )
            for e in result.entries
        ],
        ranked_model_names=list(result.ranked_model_names),
    )


@router.post("/critique", response_model=CriticVerdictResponse)
def critique_response(
    request: CritiqueRequest, fabric: AIIntelligenceFabric = Depends(get_ai_intelligence_fabric)
) -> CriticVerdictResponse:
    verdict: CriticVerdict = fabric.review(request.model_name, request.response_text)
    return CriticVerdictResponse(
        model_name=verdict.model_name,
        metrics=_to_metrics_payload(verdict.metrics),
        quality_score=verdict.quality_score,
        issues=list(verdict.issues),
    )


@router.post("/consensus", response_model=ConsensusOutcomeResponse)
def build_consensus(
    request: ConsensusRequest, fabric: AIIntelligenceFabric = Depends(get_ai_intelligence_fabric)
) -> ConsensusOutcomeResponse:
    positions = [
        ModelPosition(model_name=p.model_name, text=p.text, quality_score=p.quality_score)
        for p in request.positions
    ]
    outcome: ConsensusOutcome = fabric.build_consensus(request.topic, positions)
    return ConsensusOutcomeResponse(
        topic=outcome.topic,
        agreement_ratio=outcome.agreement_ratio,
        synthesis=outcome.synthesis,
        divergences=list(outcome.divergences),
    )


@router.post("/fuse", response_model=FusedResponsePayload)
def fuse_responses(
    request: FuseRequest, fabric: AIIntelligenceFabric = Depends(get_ai_intelligence_fabric)
) -> FusedResponsePayload:
    positions = [
        ModelPosition(model_name=p.model_name, text=p.text, quality_score=p.quality_score)
        for p in request.positions
    ]
    fused: FusedResponse = fabric.fuse(positions)
    return FusedResponsePayload(
        fused_text=fused.fused_text,
        sources=[
            FusionSourceResponse(
                model_name=s.model_name, text=s.text, citation_count=s.citation_count
            )
            for s in fused.sources
        ],
        provenance=fused.provenance,
    )


@router.post("/benchmark", response_model=BenchmarkRunResponse)
def run_benchmark(
    request: BenchmarkRunRequest, benchmark_engine: BenchmarkEngine = Depends(get_benchmark_engine)
) -> BenchmarkRunResponse:
    run: BenchmarkRun = benchmark_engine.run(
        request.model_name,
        request.response_text,
        cost_usd=request.cost_usd,
        latency_ms=request.latency_ms,
    )
    return BenchmarkRunResponse(
        model_name=run.model_name,
        quality_score=run.quality_score,
        cost_usd=run.cost_usd,
        latency_ms=run.latency_ms,
        hallucination_flags=run.hallucination_flags,
        token_count=run.token_count,
    )


@router.get("/benchmark", response_model=list[BenchmarkRunResponse])
def comparison_table(
    benchmark_engine: BenchmarkEngine = Depends(get_benchmark_engine),
) -> list[BenchmarkRunResponse]:
    return [
        BenchmarkRunResponse(
            model_name=r.model_name,
            quality_score=r.quality_score,
            cost_usd=r.cost_usd,
            latency_ms=r.latency_ms,
            hallucination_flags=r.hallucination_flags,
            token_count=r.token_count,
        )
        for r in benchmark_engine.comparison_table()
    ]


@router.get("/benchmark/{model_name}", response_model=list[BenchmarkRunResponse])
def benchmark_history(
    model_name: str, benchmark_engine: BenchmarkEngine = Depends(get_benchmark_engine)
) -> list[BenchmarkRunResponse]:
    return [
        BenchmarkRunResponse(
            model_name=r.model_name,
            quality_score=r.quality_score,
            cost_usd=r.cost_usd,
            latency_ms=r.latency_ms,
            hallucination_flags=r.hallucination_flags,
            token_count=r.token_count,
        )
        for r in benchmark_engine.history(model_name)
    ]


@router.get("/telemetry", response_model=FabricTelemetryResponse)
def get_telemetry(firm_id: str) -> FabricTelemetryResponse:
    snapshot = get_telemetry_dashboard(firm_id).snapshot()
    return FabricTelemetryResponse(
        models=[
            ModelTelemetrySnapshotResponse(
                model_name=m.model_name,
                availability=m.availability,
                quality_score=m.quality_score,
                average_latency_ms=m.average_latency_ms,
                cost_per_1k_tokens_usd=m.cost_per_1k_tokens_usd,
                error_rate=m.error_rate,
                stability_score=m.stability_score,
                average_feedback=m.average_feedback,
                total_calls=m.total_calls,
                usage_share=m.usage_share,
            )
            for m in snapshot.models
        ],
        fallback_rate=snapshot.fallback_rate,
        cache_hit_rate=snapshot.cache_hit_rate,
    )


@router.get("/costs", response_model=CostSummaryResponse)
def get_costs(
    firm_id: str,
    cost_tracker: CostTrackerEngine = Depends(get_cost_tracker_engine),
    providers: FabricProviderRegistry = Depends(get_fabric_provider_registry),
) -> CostSummaryResponse:
    return CostSummaryResponse(
        firm_id=firm_id,
        cache_hit_rate=cost_tracker.cache_hit_rate(firm_id),
        cost_by_provider={
            name: cost_tracker.cost_by_provider(firm_id, name) for name in providers.list_names()
        },
    )


@router.post("/policies", response_model=PolicyResponse)
def create_policy(
    request: PolicyCreateRequest, policy_store: PolicyStorePort = Depends(get_policy_store)
) -> PolicyResponse:
    policy = Policy(
        id=new_policy_id(),
        type=PolicyType(request.type),
        model_name=request.model_name,
        reason=request.reason,
        allowed_countries=(
            frozenset(request.allowed_countries) if request.allowed_countries is not None else None
        ),
        allowed_data_types=(
            frozenset(request.allowed_data_types)
            if request.allowed_data_types is not None
            else None
        ),
    )
    policy_store.add(policy)
    return _to_policy_response(policy)


@router.get("/policies", response_model=list[PolicyResponse])
def list_policies(
    policy_store: PolicyStorePort = Depends(get_policy_store),
) -> list[PolicyResponse]:
    return [_to_policy_response(p) for p in policy_store.list_all()]


@router.post("/policies/{policy_id}/deactivate", response_model=PolicyResponse)
def deactivate_policy(
    policy_id: str, policy_store: PolicyStorePort = Depends(get_policy_store)
) -> PolicyResponse:
    policy_store.deactivate(policy_id)
    for policy in policy_store.list_all():
        if policy.id == policy_id:
            return _to_policy_response(policy)
    raise HTTPException(status_code=404, detail=f"policy {policy_id} not found")


@router.post("/governance/evaluate", response_model=PolicyDecisionResponse)
def evaluate_governance(
    request: GovernanceEvaluateRequest,
    governance_engine: GovernanceEngine = Depends(get_governance_engine),
) -> PolicyDecisionResponse:
    decision = governance_engine.evaluate(
        request.firm_id, request.model_name, request.country, request.data_type
    )
    return PolicyDecisionResponse(
        id=decision.id,
        firm_id=decision.firm_id,
        model_name=decision.model_name,
        allowed=decision.allowed,
        reasons=list(decision.reasons),
    )


@router.get("/governance/history", response_model=list[PolicyDecisionResponse])
def governance_history(
    firm_id: str,
    model_name: str,
    governance_engine: GovernanceEngine = Depends(get_governance_engine),
) -> list[PolicyDecisionResponse]:
    return [
        PolicyDecisionResponse(
            id=d.id,
            firm_id=d.firm_id,
            model_name=d.model_name,
            allowed=d.allowed,
            reasons=list(d.reasons),
        )
        for d in governance_engine.history(firm_id, model_name)
    ]
