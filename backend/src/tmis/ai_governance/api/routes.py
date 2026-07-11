from fastapi import APIRouter, Depends, HTTPException, Response

from tmis.ai_governance.api.schemas import (
    AIAuditEntryResponse,
    AIAuditRecordRequest,
    BiasFindingResponse,
    ChainGraphEdgeResponse,
    ChainGraphNodeResponse,
    ChainStepRequest,
    ChainStepResponse,
    ComplianceCheckRequest,
    ComplianceVerdictResponse,
    ConfidenceRequest,
    ConfidenceResponse,
    DecisionRecordRequest,
    DecisionRecordResponse,
    EthicsFindingResponse,
    ExplainabilityReportResponse,
    ExplainabilityRequest,
    GovernancePolicyCreateRequest,
    GovernancePolicyResponse,
    HallucinationAlertResponse,
    IgnoredElementResponse,
    LineageExplanationResponse,
    LineageOriginRequest,
    LineageRecordResponse,
    PolicyEvaluateRequest,
    PolicyEvaluationResponse,
    ProductionOverviewResponse,
    ProvenanceRecordResponse,
    ProvenanceRequest,
    QualityRequest,
    QualityResponse,
    ReasoningChainGraphResponse,
    ReasoningChainResponse,
    RiskAssessmentRequest,
    RiskFindingResponse,
    TextScanRequest,
    TraceEntryRequest,
    TraceEntryResponse,
    ValidationDecisionEntryResponse,
    ValidationDecisionRequest,
    ValidationRequestPayload,
    ValidationRequestResponse,
)
from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.bootstrap import (
    get_ai_audit_engine,
    get_ai_governance_platform,
    get_bias_detection_engine,
    get_compliance_engine,
    get_confidence_engine,
    get_decision_record_engine,
    get_ethics_engine,
    get_explainability_engine,
    get_hallucination_detection_engine,
    get_human_validation_engine,
    get_lineage_engine,
    get_policy_engine,
    get_provenance_engine,
    get_quality_engine,
    get_reasoning_chain_engine,
    get_risk_engine,
    get_traceability_engine,
)
from tmis.ai_governance.compliance.engine import ComplianceEngine
from tmis.ai_governance.confidence.engine import GovernanceConfidenceEngine
from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
from tmis.ai_governance.decision_records.schemas import DecisionRecord
from tmis.ai_governance.ethics.engine import EthicsEngine
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.schemas import ExplainabilityReport
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType, ValidationRequest
from tmis.ai_governance.lineage.engine import LineageEngine
from tmis.ai_governance.lineage.schemas import LineageExplanation
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import (
    GovernancePolicy,
    GovernancePolicyType,
    PolicyEvaluationContext,
)
from tmis.ai_governance.provenance.engine import ProvenanceEngine
from tmis.ai_governance.provenance.schemas import (
    ProvenanceGranularity,
    ProvenanceRecord,
    SourceType,
)
from tmis.ai_governance.quality.engine import GovernanceQualityEngine
from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
from tmis.ai_governance.reasoning_chain.schemas import ChainStageType
from tmis.ai_governance.risk_engine.engine import RiskEngine
from tmis.ai_governance.traceability.engine import TraceabilityEngine
from tmis.ai_governance.traceability.schemas import TraceEntryKind

router = APIRouter(prefix="/ai-governance", tags=["ai-governance"])


def _to_decision_response(record: DecisionRecord) -> DecisionRecordResponse:
    return DecisionRecordResponse(
        id=record.id,
        context=record.context,
        objective=record.objective,
        hypotheses_considered=list(record.hypotheses_considered),
        alternatives_considered=list(record.alternatives_considered),
        decision=record.decision,
        justification=record.justification,
        impacts=list(record.impacts),
    )


def _to_explainability_response(report: ExplainabilityReport) -> ExplainabilityReportResponse:
    return ExplainabilityReportResponse(
        id=report.id,
        production_id=report.production_id,
        summary=report.summary,
        steps_followed=list(report.steps_followed),
        agents_involved=list(report.agents_involved),
        models_used=list(report.models_used),
        legal_references=list(report.legal_references),
        documents_consulted=list(report.documents_consulted),
        ignored_elements=[
            IgnoredElementResponse(description=e.description, justification=e.justification)
            for e in report.ignored_elements
        ],
    )


def _to_provenance_response(record: ProvenanceRecord) -> ProvenanceRecordResponse:
    return ProvenanceRecordResponse(
        id=record.id,
        granularity=record.granularity.value,
        locator=record.locator,
        excerpt=record.excerpt,
        source_type=record.source_type.value,
        source_reference=record.source_reference,
        produced_by_agent=record.produced_by_agent,
        produced_by_model=record.produced_by_model,
    )


def _to_trace_response(entry: object) -> TraceEntryResponse:
    return TraceEntryResponse(
        id=entry.id,  # type: ignore[attr-defined]
        kind=entry.kind.value,  # type: ignore[attr-defined]
        reference=entry.reference,  # type: ignore[attr-defined]
        detail=entry.detail,  # type: ignore[attr-defined]
    )


def _to_validation_response(request: ValidationRequest) -> ValidationRequestResponse:
    return ValidationRequestResponse(
        id=request.id,
        production_id=request.production_id,
        requested_by=request.requested_by,
        mode=request.mode.value,
        status=request.status.value,
        history=[
            ValidationDecisionEntryResponse(
                approver_id=e.approver_id,
                decision=e.decision.value,
                tier=e.tier,
                comment=e.comment,
            )
            for e in request.history
        ],
    )


def _to_lineage_response(explanation: LineageExplanation) -> LineageExplanationResponse:
    return LineageExplanationResponse(
        production_id=explanation.production_id,
        origin_records=[
            LineageRecordResponse(
                id=r.id,
                source_refs=list(r.source_refs),
                actor=r.actor,
                revised_from_id=r.revised_from_id,
            )
            for r in explanation.origin_records
        ],
        revision_chain=list(explanation.revision_chain),
    )


def _to_policy_response(policy: GovernancePolicy) -> GovernancePolicyResponse:
    return GovernancePolicyResponse(
        id=policy.id,
        firm_id=policy.firm_id,
        type=policy.type.value,
        reason=policy.reason,
        min_confidence=policy.min_confidence,
        forbidden_model_name=policy.forbidden_model_name,
        case_type=policy.case_type,
        active=policy.active,
    )


@router.post("/chain/steps", response_model=ChainStepResponse)
def record_chain_step(
    firm_id: str,
    production_id: str,
    request: ChainStepRequest,
    engine: ReasoningChainEngine = Depends(get_reasoning_chain_engine),
) -> ChainStepResponse:
    step = engine.record_step(
        firm_id,
        production_id,
        ChainStageType(request.stage),
        request.summary,
        tuple(request.references),
    )
    return ChainStepResponse(
        id=step.id, stage=step.stage.value, summary=step.summary, references=list(step.references)
    )


@router.get("/chain/{production_id}", response_model=ReasoningChainResponse)
def get_reasoning_chain(
    production_id: str,
    firm_id: str,
    engine: ReasoningChainEngine = Depends(get_reasoning_chain_engine),
) -> ReasoningChainResponse:
    chain = engine.chain_for(firm_id, production_id)
    return ReasoningChainResponse(
        id=chain.id,
        production_id=chain.production_id,
        steps=[
            ChainStepResponse(
                id=s.id, stage=s.stage.value, summary=s.summary, references=list(s.references)
            )
            for s in chain.steps
        ],
    )


@router.get("/chain/{production_id}/graph", response_model=ReasoningChainGraphResponse)
def get_reasoning_chain_graph(
    production_id: str,
    firm_id: str,
    engine: ReasoningChainEngine = Depends(get_reasoning_chain_engine),
) -> ReasoningChainGraphResponse:
    graph = engine.to_graph(firm_id, production_id)
    return ReasoningChainGraphResponse(
        nodes=[
            ChainGraphNodeResponse(id=n.id, stage=n.stage.value, label=n.label) for n in graph.nodes
        ],
        edges=[
            ChainGraphEdgeResponse(source_id=e.source_id, target_id=e.target_id)
            for e in graph.edges
        ],
    )


@router.post("/decisions", response_model=DecisionRecordResponse)
def record_decision(
    request: DecisionRecordRequest,
    engine: DecisionRecordEngine = Depends(get_decision_record_engine),
) -> DecisionRecordResponse:
    record = engine.record(
        request.firm_id,
        request.production_id,
        context=request.context,
        objective=request.objective,
        hypotheses_considered=tuple(request.hypotheses_considered),
        alternatives_considered=tuple(request.alternatives_considered),
        decision=request.decision,
        justification=request.justification,
        impacts=tuple(request.impacts),
    )
    return _to_decision_response(record)


@router.get("/decisions/{production_id}", response_model=list[DecisionRecordResponse])
def get_decisions(
    production_id: str,
    firm_id: str,
    engine: DecisionRecordEngine = Depends(get_decision_record_engine),
) -> list[DecisionRecordResponse]:
    return [_to_decision_response(r) for r in engine.history(firm_id, production_id)]


@router.post("/confidence", response_model=ConfidenceResponse)
def score_confidence(
    request: ConfidenceRequest, engine: GovernanceConfidenceEngine = Depends(get_confidence_engine)
) -> ConfidenceResponse:
    score = engine.score(
        request.production_id,
        source_quality=request.source_quality,
        reasoning_coherence=request.reasoning_coherence,
        human_validation=request.human_validation,
        multi_agent_consensus=request.multi_agent_consensus,
        model_stability=request.model_stability,
    )
    return ConfidenceResponse(
        production_id=score.production_id,
        value=score.value,
        explanation=score.explanation,
        factors=score.factors,
    )


@router.post("/risks", response_model=list[RiskFindingResponse])
def assess_risks(
    request: RiskAssessmentRequest, engine: RiskEngine = Depends(get_risk_engine)
) -> list[RiskFindingResponse]:
    findings = engine.assess(
        citation_count=request.citation_count,
        contradiction_count=request.contradiction_count,
        source_age_days=request.source_age_days,
        confidence_value=request.confidence_value,
        human_validated=request.human_validated,
    )
    return [
        RiskFindingResponse(
            id=f.id,
            category=f.category.value,
            severity=f.severity.value,
            description=f.description,
            explanation=f.explanation,
        )
        for f in findings
    ]


@router.post("/explanations", response_model=ExplainabilityReportResponse)
def generate_explanation(
    request: ExplainabilityRequest,
    engine: ExplainabilityEngine = Depends(get_explainability_engine),
) -> ExplainabilityReportResponse:
    report = engine.generate(
        request.firm_id,
        request.production_id,
        summary=request.summary,
        steps_followed=tuple(request.steps_followed),
        agents_involved=tuple(request.agents_involved),
        models_used=tuple(request.models_used),
        legal_references=tuple(request.legal_references),
        documents_consulted=tuple(request.documents_consulted),
    )
    return _to_explainability_response(report)


@router.get("/explanations/{production_id}", response_model=list[ExplainabilityReportResponse])
def get_explanations(
    production_id: str,
    firm_id: str,
    engine: ExplainabilityEngine = Depends(get_explainability_engine),
) -> list[ExplainabilityReportResponse]:
    return [_to_explainability_response(r) for r in engine.history(firm_id, production_id)]


@router.post("/provenance", response_model=ProvenanceRecordResponse)
def record_provenance(
    request: ProvenanceRequest, engine: ProvenanceEngine = Depends(get_provenance_engine)
) -> ProvenanceRecordResponse:
    record = engine.record(
        request.firm_id,
        request.production_id,
        granularity=ProvenanceGranularity(request.granularity),
        locator=request.locator,
        excerpt=request.excerpt,
        source_type=SourceType(request.source_type),
        source_reference=request.source_reference,
        produced_by_agent=request.produced_by_agent,
        produced_by_model=request.produced_by_model,
    )
    return _to_provenance_response(record)


@router.get("/provenance/{production_id}", response_model=list[ProvenanceRecordResponse])
def get_provenance(
    production_id: str, firm_id: str, engine: ProvenanceEngine = Depends(get_provenance_engine)
) -> list[ProvenanceRecordResponse]:
    return [_to_provenance_response(r) for r in engine.trace(firm_id, production_id)]


@router.post("/trace", response_model=TraceEntryResponse)
def record_trace(
    request: TraceEntryRequest, engine: TraceabilityEngine = Depends(get_traceability_engine)
) -> TraceEntryResponse:
    entry = engine.record(
        request.firm_id,
        request.production_id,
        TraceEntryKind(request.kind),
        request.reference,
        request.detail,
    )
    return _to_trace_response(entry)


@router.get("/trace/{production_id}", response_model=list[TraceEntryResponse])
def get_trace(
    production_id: str, firm_id: str, engine: TraceabilityEngine = Depends(get_traceability_engine)
) -> list[TraceEntryResponse]:
    return [_to_trace_response(e) for e in engine.trace(firm_id, production_id)]


@router.post("/lineage", response_model=LineageRecordResponse)
def record_lineage_origin(
    request: LineageOriginRequest, engine: LineageEngine = Depends(get_lineage_engine)
) -> LineageRecordResponse:
    record = engine.record_origin(
        request.firm_id,
        request.production_id,
        tuple(request.source_refs),
        request.actor,
        request.revised_from_id,
    )
    return LineageRecordResponse(
        id=record.id,
        source_refs=list(record.source_refs),
        actor=record.actor,
        revised_from_id=record.revised_from_id,
    )


@router.get("/lineage/{production_id}", response_model=LineageExplanationResponse)
def get_lineage(
    production_id: str, firm_id: str, engine: LineageEngine = Depends(get_lineage_engine)
) -> LineageExplanationResponse:
    return _to_lineage_response(engine.explain(firm_id, production_id))


@router.post("/bias-scan", response_model=list[BiasFindingResponse])
def scan_bias(
    request: TextScanRequest, engine: BiasDetectionEngine = Depends(get_bias_detection_engine)
) -> list[BiasFindingResponse]:
    return [
        BiasFindingResponse(
            id=f.id,
            detector_name=f.detector_name,
            category=f.category,
            excerpt=f.excerpt,
            description=f.description,
            explanation=f.explanation,
        )
        for f in engine.scan(request.text)
    ]


@router.post("/hallucination-scan", response_model=list[HallucinationAlertResponse])
def scan_hallucinations(
    request: TextScanRequest,
    engine: HallucinationDetectionEngine = Depends(get_hallucination_detection_engine),
) -> list[HallucinationAlertResponse]:
    return [
        HallucinationAlertResponse(
            id=a.id, excerpt=a.excerpt, reason=a.reason, recommendation=a.recommendation
        )
        for a in engine.scan(request.text)
    ]


@router.post("/ethics-scan", response_model=list[EthicsFindingResponse])
def scan_ethics(
    request: TextScanRequest, engine: EthicsEngine = Depends(get_ethics_engine)
) -> list[EthicsFindingResponse]:
    return [
        EthicsFindingResponse(
            id=f.id,
            category=f.category,
            excerpt=f.excerpt,
            description=f.description,
            explanation=f.explanation,
        )
        for f in engine.screen(request.text)
    ]


@router.post("/policies", response_model=GovernancePolicyResponse)
def create_policy(
    request: GovernancePolicyCreateRequest, engine: PolicyEngine = Depends(get_policy_engine)
) -> GovernancePolicyResponse:
    policy = engine.create_policy(
        request.firm_id,
        GovernancePolicyType(request.type),
        request.reason,
        min_confidence=request.min_confidence,
        forbidden_model_name=request.forbidden_model_name,
        case_type=request.case_type,
    )
    return _to_policy_response(policy)


@router.get("/policies", response_model=list[GovernancePolicyResponse])
def list_policies(
    firm_id: str, engine: PolicyEngine = Depends(get_policy_engine)
) -> list[GovernancePolicyResponse]:
    return [_to_policy_response(p) for p in engine.list_policies(firm_id)]


@router.post("/policies/{policy_id}/deactivate")
def deactivate_policy(
    policy_id: str, engine: PolicyEngine = Depends(get_policy_engine)
) -> dict[str, str]:
    engine.deactivate_policy(policy_id)
    return {"id": policy_id, "status": "deactivated"}


@router.post("/policies/evaluate", response_model=PolicyEvaluationResponse)
def evaluate_policies(
    request: PolicyEvaluateRequest, engine: PolicyEngine = Depends(get_policy_engine)
) -> PolicyEvaluationResponse:
    context = PolicyEvaluationContext(
        firm_id=request.firm_id,
        production_id=request.production_id,
        is_export=request.is_export,
        confidence_value=request.confidence_value,
        model_names_used=tuple(request.model_names_used),
        citation_count=request.citation_count,
        case_type=request.case_type,
        human_validated=request.human_validated,
    )
    evaluation = engine.evaluate(context)
    return PolicyEvaluationResponse(
        id=evaluation.id,
        production_id=evaluation.production_id,
        allowed=evaluation.allowed,
        reasons=list(evaluation.reasons),
    )


@router.post("/validations/simple", response_model=ValidationRequestResponse)
def request_simple_validation(
    request: ValidationRequestPayload,
    engine: HumanValidationEngine = Depends(get_human_validation_engine),
) -> ValidationRequestResponse:
    result = engine.request_simple(
        request.firm_id, request.production_id, request.requested_by, tuple(request.approver_ids)
    )
    return _to_validation_response(result)


@router.post("/validations/multiple", response_model=ValidationRequestResponse)
def request_multiple_validation(
    request: ValidationRequestPayload,
    engine: HumanValidationEngine = Depends(get_human_validation_engine),
) -> ValidationRequestResponse:
    result = engine.request_multiple(
        request.firm_id, request.production_id, request.requested_by, tuple(request.approver_ids)
    )
    return _to_validation_response(result)


@router.post("/validations/hierarchical", response_model=ValidationRequestResponse)
def request_hierarchical_validation(
    request: ValidationRequestPayload,
    engine: HumanValidationEngine = Depends(get_human_validation_engine),
) -> ValidationRequestResponse:
    tiers = tuple(tuple(tier) for tier in request.approver_tiers)
    result = engine.request_hierarchical(
        request.firm_id, request.production_id, request.requested_by, tiers
    )
    return _to_validation_response(result)


@router.post("/validations/{request_id}/decide", response_model=ValidationRequestResponse)
def decide_validation(
    request_id: str,
    request: ValidationDecisionRequest,
    engine: HumanValidationEngine = Depends(get_human_validation_engine),
) -> ValidationRequestResponse:
    try:
        result = engine.decide(
            request.firm_id,
            request_id,
            request.approver_id,
            ValidationDecisionType(request.decision),
            request.comment,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_validation_response(result)


@router.get("/validations/{production_id}", response_model=list[ValidationRequestResponse])
def get_validations(
    production_id: str,
    firm_id: str,
    engine: HumanValidationEngine = Depends(get_human_validation_engine),
) -> list[ValidationRequestResponse]:
    return [_to_validation_response(r) for r in engine.history(firm_id, production_id)]


@router.post("/audit", response_model=AIAuditEntryResponse)
def record_audit(
    request: AIAuditRecordRequest, engine: AIAuditEngine = Depends(get_ai_audit_engine)
) -> AIAuditEntryResponse:
    entry = engine.record(
        request.firm_id,
        request.production_id,
        request.actor_id,
        request.action,
        prompt=request.prompt,
        model_name=request.model_name,
        cost_usd=request.cost_usd,
        duration_ms=request.duration_ms,
        decision_id=request.decision_id,
        policy_ids=tuple(request.policy_ids),
        validation_id=request.validation_id,
    )
    return AIAuditEntryResponse(
        id=entry.id,
        production_id=entry.production_id,
        actor_id=entry.actor_id,
        action=entry.action,
        prompt=entry.prompt,
        model_name=entry.model_name,
        cost_usd=entry.cost_usd,
        duration_ms=entry.duration_ms,
        recorded_at=entry.recorded_at.isoformat(),
    )


@router.get("/audit", response_model=list[AIAuditEntryResponse])
def list_audit(
    firm_id: str, engine: AIAuditEngine = Depends(get_ai_audit_engine)
) -> list[AIAuditEntryResponse]:
    return [
        AIAuditEntryResponse(
            id=e.id,
            production_id=e.production_id,
            actor_id=e.actor_id,
            action=e.action,
            prompt=e.prompt,
            model_name=e.model_name,
            cost_usd=e.cost_usd,
            duration_ms=e.duration_ms,
            recorded_at=e.recorded_at.isoformat(),
        )
        for e in engine.list_for_firm(firm_id)
    ]


@router.get("/audit/export")
def export_audit(firm_id: str, engine: AIAuditEngine = Depends(get_ai_audit_engine)) -> Response:
    return Response(content=engine.export_csv(firm_id), media_type="text/csv")


@router.post("/compliance/check", response_model=ComplianceVerdictResponse)
def check_compliance(
    request: ComplianceCheckRequest,
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    risk_engine: RiskEngine = Depends(get_risk_engine),
    compliance_engine: ComplianceEngine = Depends(get_compliance_engine),
) -> ComplianceVerdictResponse:
    context = PolicyEvaluationContext(
        firm_id=request.firm_id,
        production_id=request.production_id,
        is_export=request.is_export,
        confidence_value=request.confidence_value,
        model_names_used=tuple(request.model_names_used),
        citation_count=request.citation_count,
        case_type=request.case_type,
        human_validated=request.human_validated,
    )
    policy_evaluation = policy_engine.evaluate(context)
    risks = risk_engine.assess(
        citation_count=request.citation_count,
        contradiction_count=request.contradiction_count,
        source_age_days=request.source_age_days,
        confidence_value=request.confidence_value,
        human_validated=request.human_validated,
    )
    verdict = compliance_engine.check(request.production_id, policy_evaluation, risks)
    return ComplianceVerdictResponse(
        production_id=verdict.production_id,
        compliant=verdict.compliant,
        blocking_reasons=list(verdict.blocking_reasons),
        warnings=list(verdict.warnings),
    )


@router.post("/quality", response_model=QualityResponse)
def evaluate_quality(
    request: QualityRequest, engine: GovernanceQualityEngine = Depends(get_quality_engine)
) -> QualityResponse:
    breakdown = engine.evaluate(
        request.production_id,
        explainability_completeness=request.explainability_completeness,
        provenance_completeness=request.provenance_completeness,
        confidence_value=request.confidence_value,
        risk_absence=request.risk_absence,
        human_validation_coverage=request.human_validation_coverage,
    )
    return QualityResponse(
        production_id=breakdown.production_id,
        explainability_completeness=breakdown.explainability_completeness,
        provenance_completeness=breakdown.provenance_completeness,
        confidence_value=breakdown.confidence_value,
        risk_absence=breakdown.risk_absence,
        human_validation_coverage=breakdown.human_validation_coverage,
        overall=breakdown.overall,
    )


@router.get("/overview/{production_id}", response_model=ProductionOverviewResponse)
def get_overview(
    production_id: str,
    firm_id: str,
    platform: AIGovernancePlatform = Depends(get_ai_governance_platform),
) -> ProductionOverviewResponse:
    overview = platform.overview(firm_id, production_id)
    return ProductionOverviewResponse(
        production_id=overview.production_id,
        reasoning_chain=ReasoningChainResponse(
            id=overview.reasoning_chain.id,
            production_id=overview.reasoning_chain.production_id,
            steps=[
                ChainStepResponse(
                    id=s.id, stage=s.stage.value, summary=s.summary, references=list(s.references)
                )
                for s in overview.reasoning_chain.steps
            ],
        ),
        provenance=[_to_provenance_response(p) for p in overview.provenance],
        trace=[_to_trace_response(t) for t in overview.trace],
        decisions=[_to_decision_response(d) for d in overview.decisions],
        validations=[_to_validation_response(v) for v in overview.validations],
        lineage=_to_lineage_response(overview.lineage),
        explainability=(
            _to_explainability_response(overview.explainability)
            if overview.explainability is not None
            else None
        ),
    )
