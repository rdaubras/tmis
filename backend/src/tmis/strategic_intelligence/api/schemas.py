from pydantic import BaseModel, Field


class StrategyGenerateRequest(BaseModel):
    case_id: str
    question: str
    hypotheses: tuple[str, ...] = ()
    main_arguments: tuple[str, ...] = ()
    counter_arguments: tuple[str, ...] = ()
    available_evidence: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    candidate_types: tuple[str, ...] | None = None


class StrategyResponse(BaseModel):
    id: str
    case_id: str
    strategy_type: str
    objective: str
    hypotheses: tuple[str, ...]
    main_arguments: tuple[str, ...]
    counter_arguments: tuple[str, ...]
    available_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    recommended_steps: tuple[str, ...]
    risks: tuple[str, ...]
    confidence: float
    limitations: tuple[str, ...]


class HypothesisCreateRequest(BaseModel):
    firm_id: str
    case_id: str
    description: str
    parent_ids: tuple[str, ...] = ()


class HypothesisResponse(BaseModel):
    id: str
    case_id: str
    description: str
    status: str
    parent_ids: tuple[str, ...]


class HypothesisCompareRequest(BaseModel):
    firm_id: str
    hypothesis_a_id: str
    hypothesis_b_id: str


class HypothesisComparisonResponse(BaseModel):
    hypothesis_a_id: str
    hypothesis_b_id: str
    similarity: float
    shared_terms: tuple[str, ...]
    differences: tuple[str, ...]


class HypothesisMergeRequest(BaseModel):
    firm_id: str
    hypothesis_a_id: str
    hypothesis_b_id: str
    actor: str
    merged_description: str | None = None


class HypothesisActionRequest(BaseModel):
    firm_id: str
    actor: str
    reason: str | None = None


class HypothesisEventResponse(BaseModel):
    id: str
    hypothesis_id: str
    from_status: str
    to_status: str
    actor: str
    reason: str | None


class ScenarioBuildRequest(BaseModel):
    base_case_id: str
    context: str
    hypotheses: tuple[str, ...] = ()


class ScenarioResponse(BaseModel):
    id: str
    base_case_id: str
    scenario_type: str
    context: str
    hypotheses: tuple[str, ...]
    expected_impacts: tuple[str, ...]
    limitations: tuple[str, ...]


class RiskMatrixEvaluateRequest(BaseModel):
    strategy_id: str
    documentary_solidity: float = Field(ge=0.0, le=1.0)
    reasoning_coherence: float = Field(ge=0.0, le=1.0)
    evidence_dependency: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    requires_human_validation: bool


class RiskMatrixResultResponse(BaseModel):
    strategy_id: str
    score: float
    explanation: str
    factors: dict[str, float]


class OpportunityFindRequest(BaseModel):
    strategy_id: str
    main_arguments: tuple[str, ...] = ()
    unused_hypotheses: tuple[str, ...] = ()
    available_evidence: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    clauses_to_verify: tuple[str, ...] = ()


class OpportunityFindingResponse(BaseModel):
    id: str
    category: str
    description: str
    justification: str


class EvidenceGapIdentifyRequest(BaseModel):
    strategy_id: str
    missing_evidence: tuple[str, ...]
    context: str = ""


class EvidenceGapResponse(BaseModel):
    missing_evidence: str
    interest: str
    potential_impact: str


class ActionStepAddRequest(BaseModel):
    firm_id: str
    strategy_id: str
    description: str
    category: str
    order: int | None = None


class ActionStepResponse(BaseModel):
    id: str
    strategy_id: str
    description: str
    category: str
    order: int
    done: bool


class ActionStepReorderRequest(BaseModel):
    firm_id: str
    strategy_id: str
    ordered_step_ids: tuple[str, ...]


class StrategyMetricsPayload(BaseModel):
    strategy_id: str
    strategy_type: str
    confidence: float
    coverage: float
    risk_score: float
    effort: float
    estimated_duration_days: int


class DecisionSupportCompareRequest(BaseModel):
    metrics: list[StrategyMetricsPayload]


class StrategyComparisonResponse(BaseModel):
    metrics: tuple[StrategyMetricsPayload, ...]
    disclaimer: str


class TimelineEntryPayload(BaseModel):
    date: str
    kind: str
    description: str
    reference: str


class TimelineBuildRequest(BaseModel):
    entries: list[TimelineEntryPayload]


class ProbabilityAssessRequest(BaseModel):
    element_description: str
    supporting_count: int = Field(ge=0)
    contradicting_count: int = Field(ge=0)


class ProbabilityAssessmentResponse(BaseModel):
    element_description: str
    likelihood: str
    rationale: str


class SimulationRunRequest(BaseModel):
    base_case_id: str
    strategy_texts: dict[str, str]
    hypothetical_changes: tuple[str, ...]


class SimulationResultResponse(BaseModel):
    scenario_id: str
    affected_strategy_ids: tuple[str, ...]
    notes: tuple[str, ...]


class TradeoffCompareRequest(BaseModel):
    strategy_a_id: str
    strategy_b_id: str
    advantages_a: tuple[str, ...] = ()
    advantages_b: tuple[str, ...] = ()
    risks_a: tuple[str, ...] = ()
    risks_b: tuple[str, ...] = ()


class TradeoffAnalysisResponse(BaseModel):
    strategy_a_id: str
    strategy_b_id: str
    advantages_a: tuple[str, ...]
    advantages_b: tuple[str, ...]
    shared_risks: tuple[str, ...]


class PlaybookStepResponse(BaseModel):
    order: int
    title: str
    description: str


class PlaybookResponse(BaseModel):
    id: str
    case_type: str
    title: str
    steps: tuple[PlaybookStepResponse, ...]


class ReviewRequestRequest(BaseModel):
    firm_id: str
    strategy_id: str
    requested_by: str
    approver_ids: tuple[str, ...]


class ReviewDecideRequest(BaseModel):
    firm_id: str
    approver_id: str
    decision: str
    comment: str | None = None


class ValidationRequestResponse(BaseModel):
    id: str
    production_id: str
    requested_by: str
    mode: str
    status: str


class LearningRecordRequest(BaseModel):
    firm_id: str
    case_id: str
    strategy_id: str
    strategy_type: str
    outcome: str
    actor: str
    comment: str = ""


class LearningRecordResponse(BaseModel):
    id: str
    case_id: str
    strategy_id: str
    strategy_type: str
    outcome: str
    actor: str
    comment: str


class CaseStrategicOverviewResponse(BaseModel):
    case_id: str
    hypotheses: tuple[HypothesisResponse, ...]
    learning_history: tuple[LearningRecordResponse, ...]


class StrategyOverviewResponse(BaseModel):
    strategy_id: str
    action_steps: tuple[ActionStepResponse, ...]
    review_history: tuple[ValidationRequestResponse, ...]
    is_validated: bool
