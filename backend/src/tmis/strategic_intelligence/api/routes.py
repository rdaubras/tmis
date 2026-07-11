from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.strategic_intelligence.action_planner.engine import ActionPlannerEngine
from tmis.strategic_intelligence.api.schemas import (
    ActionStepAddRequest,
    ActionStepReorderRequest,
    ActionStepResponse,
    CaseStrategicOverviewResponse,
    DecisionSupportCompareRequest,
    EvidenceGapIdentifyRequest,
    EvidenceGapResponse,
    HypothesisActionRequest,
    HypothesisCompareRequest,
    HypothesisComparisonResponse,
    HypothesisCreateRequest,
    HypothesisEventResponse,
    HypothesisMergeRequest,
    HypothesisResponse,
    LearningRecordRequest,
    LearningRecordResponse,
    OpportunityFindingResponse,
    OpportunityFindRequest,
    PlaybookResponse,
    PlaybookStepResponse,
    ProbabilityAssessmentResponse,
    ProbabilityAssessRequest,
    ReviewDecideRequest,
    ReviewRequestRequest,
    RiskMatrixEvaluateRequest,
    RiskMatrixResultResponse,
    ScenarioBuildRequest,
    ScenarioResponse,
    SimulationResultResponse,
    SimulationRunRequest,
    StrategyComparisonResponse,
    StrategyGenerateRequest,
    StrategyMetricsPayload,
    StrategyOverviewResponse,
    StrategyResponse,
    TimelineBuildRequest,
    TimelineEntryPayload,
    TradeoffAnalysisResponse,
    TradeoffCompareRequest,
    ValidationRequestResponse,
)
from tmis.strategic_intelligence.bootstrap import (
    get_action_planner_engine,
    get_decision_support_engine,
    get_evidence_gap_engine,
    get_hypothesis_lab_engine,
    get_learning_engine,
    get_opportunity_engine,
    get_playbook_adapter,
    get_probability_engine,
    get_risk_matrix_engine,
    get_scenario_builder_engine,
    get_simulation_engine,
    get_strategic_intelligence_platform,
    get_strategy_engine,
    get_strategy_review_adapter,
    get_timeline_engine,
    get_tradeoff_engine,
)
from tmis.strategic_intelligence.decision_support.engine import DecisionSupportEngine
from tmis.strategic_intelligence.decision_support.schemas import StrategyMetrics
from tmis.strategic_intelligence.evidence_gap.engine import EvidenceGapEngine
from tmis.strategic_intelligence.hypothesis_lab.engine import HypothesisLabEngine
from tmis.strategic_intelligence.hypothesis_lab.schemas import InvalidHypothesisTransitionError
from tmis.strategic_intelligence.learning.engine import LearningEngine
from tmis.strategic_intelligence.learning.schemas import StrategyOutcome
from tmis.strategic_intelligence.opportunity_engine.engine import OpportunityEngine
from tmis.strategic_intelligence.overview import StrategicIntelligencePlatform
from tmis.strategic_intelligence.playbooks.adapter import PlaybookAdapter
from tmis.strategic_intelligence.probability.engine import ProbabilityEngine
from tmis.strategic_intelligence.review.adapter import StrategyReviewAdapter
from tmis.strategic_intelligence.risk_matrix.engine import RiskMatrixEngine
from tmis.strategic_intelligence.scenario_builder.engine import ScenarioBuilderEngine
from tmis.strategic_intelligence.simulation.engine import SimulationEngine
from tmis.strategic_intelligence.strategy_engine.engine import StrategyEngine
from tmis.strategic_intelligence.timeline.engine import TimelineEngine
from tmis.strategic_intelligence.timeline.schemas import StrategicTimelineEntry, TimelineEntryKind
from tmis.strategic_intelligence.tradeoffs.engine import TradeoffEngine

router = APIRouter(prefix="/strategic-intelligence", tags=["strategic-intelligence"])


@router.post("/strategies/generate", response_model=list[StrategyResponse])
def generate_strategies(
    payload: StrategyGenerateRequest,
    engine: StrategyEngine = Depends(get_strategy_engine),
) -> list[StrategyResponse]:
    strategies = engine.generate(
        case_id=payload.case_id,
        question=payload.question,
        hypotheses=payload.hypotheses,
        main_arguments=payload.main_arguments,
        counter_arguments=payload.counter_arguments,
        available_evidence=payload.available_evidence,
        missing_evidence=payload.missing_evidence,
        candidate_types=payload.candidate_types,
    )
    return [StrategyResponse(**asdict(s)) for s in strategies]


@router.post("/hypotheses", response_model=HypothesisResponse)
def create_hypothesis(
    payload: HypothesisCreateRequest,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> HypothesisResponse:
    hypothesis = engine.create(
        payload.firm_id, payload.case_id, payload.description, payload.parent_ids
    )
    return HypothesisResponse(
        id=hypothesis.id,
        case_id=hypothesis.case_id,
        description=hypothesis.description,
        status=hypothesis.status.value,
        parent_ids=hypothesis.parent_ids,
    )


@router.get("/hypotheses/{case_id}", response_model=list[HypothesisResponse])
def list_hypotheses(
    case_id: str,
    firm_id: str,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> list[HypothesisResponse]:
    return [
        HypothesisResponse(
            id=h.id, case_id=h.case_id, description=h.description,
            status=h.status.value, parent_ids=h.parent_ids,
        )
        for h in engine.list_for_case(firm_id, case_id)
    ]


@router.post("/hypotheses/compare", response_model=HypothesisComparisonResponse)
def compare_hypotheses(
    payload: HypothesisCompareRequest,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> HypothesisComparisonResponse:
    try:
        comparison = engine.compare(
            payload.firm_id, payload.hypothesis_a_id, payload.hypothesis_b_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return HypothesisComparisonResponse(**asdict(comparison))


@router.post("/hypotheses/merge", response_model=HypothesisResponse)
def merge_hypotheses(
    payload: HypothesisMergeRequest,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> HypothesisResponse:
    try:
        merged = engine.merge(
            payload.firm_id,
            payload.hypothesis_a_id,
            payload.hypothesis_b_id,
            payload.actor,
            payload.merged_description,
        )
    except (KeyError, InvalidHypothesisTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HypothesisResponse(
        id=merged.id, case_id=merged.case_id, description=merged.description,
        status=merged.status.value, parent_ids=merged.parent_ids,
    )


@router.post("/hypotheses/{hypothesis_id}/invalidate", response_model=HypothesisResponse)
def invalidate_hypothesis(
    hypothesis_id: str,
    payload: HypothesisActionRequest,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> HypothesisResponse:
    try:
        hypothesis = engine.invalidate(
            payload.firm_id, hypothesis_id, payload.actor, payload.reason or ""
        )
    except (KeyError, InvalidHypothesisTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HypothesisResponse(
        id=hypothesis.id, case_id=hypothesis.case_id, description=hypothesis.description,
        status=hypothesis.status.value, parent_ids=hypothesis.parent_ids,
    )


@router.post("/hypotheses/{hypothesis_id}/archive", response_model=HypothesisResponse)
def archive_hypothesis(
    hypothesis_id: str,
    payload: HypothesisActionRequest,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> HypothesisResponse:
    try:
        hypothesis = engine.archive(payload.firm_id, hypothesis_id, payload.actor, payload.reason)
    except (KeyError, InvalidHypothesisTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return HypothesisResponse(
        id=hypothesis.id, case_id=hypothesis.case_id, description=hypothesis.description,
        status=hypothesis.status.value, parent_ids=hypothesis.parent_ids,
    )


@router.get("/hypotheses/{hypothesis_id}/history", response_model=list[HypothesisEventResponse])
def hypothesis_history(
    hypothesis_id: str,
    firm_id: str,
    engine: HypothesisLabEngine = Depends(get_hypothesis_lab_engine),
) -> list[HypothesisEventResponse]:
    return [
        HypothesisEventResponse(
            id=e.id, hypothesis_id=e.hypothesis_id, from_status=e.from_status.value,
            to_status=e.to_status.value, actor=e.actor, reason=e.reason,
        )
        for e in engine.history(firm_id, hypothesis_id)
    ]


@router.post("/scenarios", response_model=list[ScenarioResponse])
def build_scenarios(
    payload: ScenarioBuildRequest,
    engine: ScenarioBuilderEngine = Depends(get_scenario_builder_engine),
) -> list[ScenarioResponse]:
    scenarios = engine.build_scenarios(payload.base_case_id, payload.context, payload.hypotheses)
    return [ScenarioResponse(**asdict(s)) for s in scenarios]


@router.post("/risk-matrix/evaluate", response_model=RiskMatrixResultResponse)
def evaluate_risk_matrix(
    payload: RiskMatrixEvaluateRequest,
    engine: RiskMatrixEngine = Depends(get_risk_matrix_engine),
) -> RiskMatrixResultResponse:
    result = engine.evaluate(
        payload.strategy_id,
        documentary_solidity=payload.documentary_solidity,
        reasoning_coherence=payload.reasoning_coherence,
        evidence_dependency=payload.evidence_dependency,
        uncertainty=payload.uncertainty,
        requires_human_validation=payload.requires_human_validation,
    )
    return RiskMatrixResultResponse(**asdict(result))


@router.post("/opportunities", response_model=list[OpportunityFindingResponse])
def find_opportunities(
    payload: OpportunityFindRequest,
    engine: OpportunityEngine = Depends(get_opportunity_engine),
) -> list[OpportunityFindingResponse]:
    findings = engine.find(
        payload.strategy_id,
        main_arguments=payload.main_arguments,
        unused_hypotheses=payload.unused_hypotheses,
        available_evidence=payload.available_evidence,
        missing_evidence=payload.missing_evidence,
        clauses_to_verify=payload.clauses_to_verify,
    )
    return [OpportunityFindingResponse(**asdict(f)) for f in findings]


@router.post("/evidence-gaps", response_model=list[EvidenceGapResponse])
def identify_evidence_gaps(
    payload: EvidenceGapIdentifyRequest,
    engine: EvidenceGapEngine = Depends(get_evidence_gap_engine),
) -> list[EvidenceGapResponse]:
    gaps = engine.identify(payload.strategy_id, payload.missing_evidence, context=payload.context)
    return [EvidenceGapResponse(**asdict(g)) for g in gaps]


@router.post("/action-plan/steps", response_model=ActionStepResponse)
def add_action_step(
    payload: ActionStepAddRequest,
    engine: ActionPlannerEngine = Depends(get_action_planner_engine),
) -> ActionStepResponse:
    step = engine.add_step(
        payload.firm_id, payload.strategy_id, payload.description, payload.category, payload.order
    )
    return ActionStepResponse(
        id=step.id, strategy_id=step.strategy_id, description=step.description,
        category=step.category, order=step.order, done=step.done,
    )


@router.delete("/action-plan/steps/{step_id}")
def remove_action_step(
    step_id: str,
    firm_id: str,
    engine: ActionPlannerEngine = Depends(get_action_planner_engine),
) -> dict[str, bool]:
    engine.remove_step(firm_id, step_id)
    return {"removed": True}


@router.post("/action-plan/steps/{step_id}/done", response_model=ActionStepResponse)
def mark_action_step_done(
    step_id: str,
    firm_id: str,
    done: bool = True,
    engine: ActionPlannerEngine = Depends(get_action_planner_engine),
) -> ActionStepResponse:
    try:
        step = engine.mark_done(firm_id, step_id, done)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ActionStepResponse(
        id=step.id, strategy_id=step.strategy_id, description=step.description,
        category=step.category, order=step.order, done=step.done,
    )


@router.post("/action-plan/reorder")
def reorder_action_plan(
    payload: ActionStepReorderRequest,
    engine: ActionPlannerEngine = Depends(get_action_planner_engine),
) -> dict[str, bool]:
    try:
        engine.reorder(payload.firm_id, payload.strategy_id, payload.ordered_step_ids)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"reordered": True}


@router.get("/action-plan/{strategy_id}", response_model=list[ActionStepResponse])
def list_action_plan(
    strategy_id: str,
    firm_id: str,
    engine: ActionPlannerEngine = Depends(get_action_planner_engine),
) -> list[ActionStepResponse]:
    return [
        ActionStepResponse(
            id=s.id, strategy_id=s.strategy_id, description=s.description,
            category=s.category, order=s.order, done=s.done,
        )
        for s in engine.list_for_strategy(firm_id, strategy_id)
    ]


@router.post("/decision-support/compare", response_model=StrategyComparisonResponse)
def compare_strategies(
    payload: DecisionSupportCompareRequest,
    engine: DecisionSupportEngine = Depends(get_decision_support_engine),
) -> StrategyComparisonResponse:
    metrics = [StrategyMetrics(**m.model_dump()) for m in payload.metrics]
    comparison = engine.compare(metrics)
    return StrategyComparisonResponse(
        metrics=tuple(StrategyMetricsPayload(**asdict(m)) for m in comparison.metrics),
        disclaimer=comparison.disclaimer,
    )


@router.post("/timeline/build", response_model=list[TimelineEntryPayload])
def build_timeline(
    payload: TimelineBuildRequest,
    engine: TimelineEngine = Depends(get_timeline_engine),
) -> list[TimelineEntryPayload]:
    entries = [
        StrategicTimelineEntry(
            date=e.date, kind=TimelineEntryKind(e.kind),
            description=e.description, reference=e.reference,
        )
        for e in payload.entries
    ]
    sorted_entries = engine.build(entries)
    return [
        TimelineEntryPayload(
            date=e.date, kind=e.kind.value, description=e.description, reference=e.reference
        )
        for e in sorted_entries
    ]


@router.post("/probability/assess", response_model=ProbabilityAssessmentResponse)
def assess_probability(
    payload: ProbabilityAssessRequest,
    engine: ProbabilityEngine = Depends(get_probability_engine),
) -> ProbabilityAssessmentResponse:
    assessment = engine.assess(
        payload.element_description,
        supporting_count=payload.supporting_count,
        contradicting_count=payload.contradicting_count,
    )
    return ProbabilityAssessmentResponse(
        element_description=assessment.element_description,
        likelihood=assessment.likelihood.value,
        rationale=assessment.rationale,
    )


@router.post("/simulation/run", response_model=SimulationResultResponse)
def run_simulation(
    payload: SimulationRunRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationResultResponse:
    result = engine.run(payload.base_case_id, payload.strategy_texts, payload.hypothetical_changes)
    return SimulationResultResponse(**asdict(result))


@router.post("/tradeoffs/compare", response_model=TradeoffAnalysisResponse)
def compare_tradeoffs(
    payload: TradeoffCompareRequest,
    engine: TradeoffEngine = Depends(get_tradeoff_engine),
) -> TradeoffAnalysisResponse:
    analysis = engine.compare(
        payload.strategy_a_id,
        payload.strategy_b_id,
        advantages_a=payload.advantages_a,
        advantages_b=payload.advantages_b,
        risks_a=payload.risks_a,
        risks_b=payload.risks_b,
    )
    return TradeoffAnalysisResponse(**asdict(analysis))


@router.get("/playbooks", response_model=list[PlaybookResponse])
def find_playbooks(
    firm_id: str,
    case_type: str,
    adapter: PlaybookAdapter = Depends(get_playbook_adapter),
) -> list[PlaybookResponse]:
    playbooks = adapter.find_playbooks_for_case_type(firm_id, case_type)
    return [
        PlaybookResponse(
            id=p.id,
            case_type=p.case_type,
            title=p.title,
            steps=tuple(
                PlaybookStepResponse(order=s.order, title=s.title, description=s.description)
                for s in p.steps
            ),
        )
        for p in playbooks
    ]


@router.post("/review/request", response_model=ValidationRequestResponse)
def request_review(
    payload: ReviewRequestRequest,
    adapter: StrategyReviewAdapter = Depends(get_strategy_review_adapter),
) -> ValidationRequestResponse:
    request = adapter.request_review(
        payload.firm_id, payload.strategy_id, payload.requested_by, payload.approver_ids
    )
    return ValidationRequestResponse(
        id=request.id, production_id=request.production_id,
        requested_by=request.requested_by, mode=request.mode.value, status=request.status.value,
    )


@router.post("/review/{request_id}/decide", response_model=ValidationRequestResponse)
def decide_review(
    request_id: str,
    payload: ReviewDecideRequest,
    adapter: StrategyReviewAdapter = Depends(get_strategy_review_adapter),
) -> ValidationRequestResponse:
    try:
        decision = ValidationDecisionType(payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        request = adapter.decide(
            payload.firm_id, request_id, payload.approver_id, decision, payload.comment
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ValidationRequestResponse(
        id=request.id, production_id=request.production_id,
        requested_by=request.requested_by, mode=request.mode.value, status=request.status.value,
    )


@router.get("/review/{strategy_id}", response_model=list[ValidationRequestResponse])
def review_history(
    strategy_id: str,
    firm_id: str,
    adapter: StrategyReviewAdapter = Depends(get_strategy_review_adapter),
) -> list[ValidationRequestResponse]:
    return [
        ValidationRequestResponse(
            id=r.id, production_id=r.production_id,
            requested_by=r.requested_by, mode=r.mode.value, status=r.status.value,
        )
        for r in adapter.history(firm_id, strategy_id)
    ]


@router.post("/learning/outcomes", response_model=LearningRecordResponse)
def record_learning_outcome(
    payload: LearningRecordRequest,
    engine: LearningEngine = Depends(get_learning_engine),
) -> LearningRecordResponse:
    try:
        outcome = StrategyOutcome(payload.outcome)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record = engine.record_outcome(
        payload.firm_id, payload.case_id, payload.strategy_id,
        payload.strategy_type, outcome, payload.actor, payload.comment,
    )
    return LearningRecordResponse(
        id=record.id, case_id=record.case_id, strategy_id=record.strategy_id,
        strategy_type=record.strategy_type, outcome=record.outcome.value,
        actor=record.actor, comment=record.comment,
    )


@router.get("/learning/{case_id}", response_model=list[LearningRecordResponse])
def learning_history_for_case(
    case_id: str,
    firm_id: str,
    engine: LearningEngine = Depends(get_learning_engine),
) -> list[LearningRecordResponse]:
    return [
        LearningRecordResponse(
            id=r.id, case_id=r.case_id, strategy_id=r.strategy_id,
            strategy_type=r.strategy_type, outcome=r.outcome.value,
            actor=r.actor, comment=r.comment,
        )
        for r in engine.history_for_case(firm_id, case_id)
    ]


@router.get("/learning/acceptance-rate/{firm_id}", response_model=dict[str, float])
def learning_acceptance_rate(
    firm_id: str,
    engine: LearningEngine = Depends(get_learning_engine),
) -> dict[str, float]:
    return engine.acceptance_rate_by_type(firm_id)


@router.get("/overview/case/{case_id}", response_model=CaseStrategicOverviewResponse)
def case_overview(
    case_id: str,
    firm_id: str,
    platform: StrategicIntelligencePlatform = Depends(get_strategic_intelligence_platform),
) -> CaseStrategicOverviewResponse:
    overview = platform.case_overview(firm_id, case_id)
    return CaseStrategicOverviewResponse(
        case_id=overview.case_id,
        hypotheses=tuple(
            HypothesisResponse(
                id=h.id, case_id=h.case_id, description=h.description,
                status=h.status.value, parent_ids=h.parent_ids,
            )
            for h in overview.hypotheses
        ),
        learning_history=tuple(
            LearningRecordResponse(
                id=r.id, case_id=r.case_id, strategy_id=r.strategy_id,
                strategy_type=r.strategy_type, outcome=r.outcome.value,
                actor=r.actor, comment=r.comment,
            )
            for r in overview.learning_history
        ),
    )


@router.get("/overview/strategy/{strategy_id}", response_model=StrategyOverviewResponse)
def strategy_overview(
    strategy_id: str,
    firm_id: str,
    platform: StrategicIntelligencePlatform = Depends(get_strategic_intelligence_platform),
) -> StrategyOverviewResponse:
    overview = platform.strategy_overview(firm_id, strategy_id)
    return StrategyOverviewResponse(
        strategy_id=overview.strategy_id,
        action_steps=tuple(
            ActionStepResponse(
                id=s.id, strategy_id=s.strategy_id, description=s.description,
                category=s.category, order=s.order, done=s.done,
            )
            for s in overview.action_steps
        ),
        review_history=tuple(
            ValidationRequestResponse(
                id=r.id, production_id=r.production_id,
                requested_by=r.requested_by, mode=r.mode.value, status=r.status.value,
            )
            for r in overview.review_history
        ),
        is_validated=overview.is_validated,
    )
