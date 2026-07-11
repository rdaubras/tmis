from pydantic import BaseModel


class ChainStepRequest(BaseModel):
    stage: str
    summary: str
    references: list[str] = []


class ChainStepResponse(BaseModel):
    id: str
    stage: str
    summary: str
    references: list[str]


class ReasoningChainResponse(BaseModel):
    id: str
    production_id: str
    steps: list[ChainStepResponse]


class ChainGraphNodeResponse(BaseModel):
    id: str
    stage: str
    label: str


class ChainGraphEdgeResponse(BaseModel):
    source_id: str
    target_id: str


class ReasoningChainGraphResponse(BaseModel):
    nodes: list[ChainGraphNodeResponse]
    edges: list[ChainGraphEdgeResponse]


class DecisionRecordRequest(BaseModel):
    firm_id: str
    production_id: str
    context: str
    objective: str
    hypotheses_considered: list[str] = []
    alternatives_considered: list[str] = []
    decision: str
    justification: str
    impacts: list[str] = []


class DecisionRecordResponse(BaseModel):
    id: str
    context: str
    objective: str
    hypotheses_considered: list[str]
    alternatives_considered: list[str]
    decision: str
    justification: str
    impacts: list[str]


class ConfidenceRequest(BaseModel):
    production_id: str
    source_quality: float
    reasoning_coherence: float
    human_validation: float
    multi_agent_consensus: float
    model_stability: float


class ConfidenceResponse(BaseModel):
    production_id: str
    value: float
    explanation: str
    factors: dict[str, float]


class RiskAssessmentRequest(BaseModel):
    citation_count: int
    contradiction_count: int
    source_age_days: int | None = None
    confidence_value: float
    human_validated: bool


class RiskFindingResponse(BaseModel):
    id: str
    category: str
    severity: str
    description: str
    explanation: str


class ExplainabilityRequest(BaseModel):
    firm_id: str
    production_id: str
    summary: str
    steps_followed: list[str]
    agents_involved: list[str] = []
    models_used: list[str] = []
    legal_references: list[str] = []
    documents_consulted: list[str] = []


class IgnoredElementResponse(BaseModel):
    description: str
    justification: str


class ExplainabilityReportResponse(BaseModel):
    id: str
    production_id: str
    summary: str
    steps_followed: list[str]
    agents_involved: list[str]
    models_used: list[str]
    legal_references: list[str]
    documents_consulted: list[str]
    ignored_elements: list[IgnoredElementResponse]


class ProvenanceRequest(BaseModel):
    firm_id: str
    production_id: str
    granularity: str
    locator: str
    excerpt: str
    source_type: str
    source_reference: str
    produced_by_agent: str | None = None
    produced_by_model: str | None = None


class ProvenanceRecordResponse(BaseModel):
    id: str
    granularity: str
    locator: str
    excerpt: str
    source_type: str
    source_reference: str
    produced_by_agent: str | None
    produced_by_model: str | None


class TraceEntryRequest(BaseModel):
    firm_id: str
    production_id: str
    kind: str
    reference: str
    detail: str


class TraceEntryResponse(BaseModel):
    id: str
    kind: str
    reference: str
    detail: str


class LineageOriginRequest(BaseModel):
    firm_id: str
    production_id: str
    source_refs: list[str]
    actor: str
    revised_from_id: str | None = None


class LineageRecordResponse(BaseModel):
    id: str
    source_refs: list[str]
    actor: str
    revised_from_id: str | None


class LineageExplanationResponse(BaseModel):
    production_id: str
    origin_records: list[LineageRecordResponse]
    revision_chain: list[str]


class TextScanRequest(BaseModel):
    text: str


class BiasFindingResponse(BaseModel):
    id: str
    detector_name: str
    category: str
    excerpt: str
    description: str
    explanation: str


class HallucinationAlertResponse(BaseModel):
    id: str
    excerpt: str
    reason: str
    recommendation: str


class EthicsFindingResponse(BaseModel):
    id: str
    category: str
    excerpt: str
    description: str
    explanation: str


class GovernancePolicyCreateRequest(BaseModel):
    firm_id: str
    type: str
    reason: str
    min_confidence: float | None = None
    forbidden_model_name: str | None = None
    case_type: str | None = None


class GovernancePolicyResponse(BaseModel):
    id: str
    firm_id: str
    type: str
    reason: str
    min_confidence: float | None
    forbidden_model_name: str | None
    case_type: str | None
    active: bool


class PolicyEvaluateRequest(BaseModel):
    firm_id: str
    production_id: str
    is_export: bool = False
    confidence_value: float | None = None
    model_names_used: list[str] = []
    citation_count: int | None = None
    case_type: str | None = None
    human_validated: bool = False


class PolicyEvaluationResponse(BaseModel):
    id: str
    production_id: str
    allowed: bool
    reasons: list[str]


class ValidationRequestPayload(BaseModel):
    firm_id: str
    production_id: str
    requested_by: str
    approver_ids: list[str] = []
    approver_tiers: list[list[str]] = []


class ValidationDecisionRequest(BaseModel):
    firm_id: str
    approver_id: str
    decision: str
    comment: str | None = None


class ValidationDecisionEntryResponse(BaseModel):
    approver_id: str
    decision: str
    tier: int
    comment: str | None


class ValidationRequestResponse(BaseModel):
    id: str
    production_id: str
    requested_by: str
    mode: str
    status: str
    history: list[ValidationDecisionEntryResponse]


class AIAuditRecordRequest(BaseModel):
    firm_id: str
    production_id: str
    actor_id: str
    action: str
    prompt: str | None = None
    model_name: str | None = None
    cost_usd: float | None = None
    duration_ms: float | None = None
    decision_id: str | None = None
    policy_ids: list[str] = []
    validation_id: str | None = None


class AIAuditEntryResponse(BaseModel):
    id: str
    production_id: str
    actor_id: str
    action: str
    prompt: str | None
    model_name: str | None
    cost_usd: float | None
    duration_ms: float | None
    recorded_at: str


class ComplianceCheckRequest(BaseModel):
    firm_id: str
    production_id: str
    is_export: bool = False
    confidence_value: float = 1.0
    model_names_used: list[str] = []
    citation_count: int = 0
    contradiction_count: int = 0
    source_age_days: int | None = None
    case_type: str | None = None
    human_validated: bool = False


class ComplianceVerdictResponse(BaseModel):
    production_id: str
    compliant: bool
    blocking_reasons: list[str]
    warnings: list[str]


class QualityRequest(BaseModel):
    production_id: str
    explainability_completeness: float
    provenance_completeness: float
    confidence_value: float
    risk_absence: float
    human_validation_coverage: float


class QualityResponse(BaseModel):
    production_id: str
    explainability_completeness: float
    provenance_completeness: float
    confidence_value: float
    risk_absence: float
    human_validation_coverage: float
    overall: float


class ReportSectionResponse(BaseModel):
    title: str
    content: str


class GovernanceReportResponse(BaseModel):
    id: str
    type: str
    production_id: str | None
    title: str
    sections: list[ReportSectionResponse]


class ProductionOverviewResponse(BaseModel):
    production_id: str
    reasoning_chain: ReasoningChainResponse
    provenance: list[ProvenanceRecordResponse]
    trace: list[TraceEntryResponse]
    decisions: list[DecisionRecordResponse]
    validations: list[ValidationRequestResponse]
    lineage: LineageExplanationResponse
    explainability: ExplainabilityReportResponse | None
