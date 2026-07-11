from pydantic import BaseModel


class ModelDescriptorResponse(BaseModel):
    name: str
    version: str
    provider: str
    cost_per_1k_tokens_usd: float
    avg_latency_ms: float
    max_context_tokens: int
    capabilities: list[str]
    profiles: list[str]
    availability: bool
    quality_score: float
    legal_score: float
    drafting_score: float
    research_score: float
    reasoning_score: float


class RoutingRequestPayload(BaseModel):
    firm_id: str
    task_type: str
    prompt: str
    profile: str | None = None
    target_cost_usd: float | None = None
    max_latency_ms: float | None = None
    min_quality_score: float = 0.0
    country: str | None = None
    data_type: str | None = None


class RoutingDecisionResponse(BaseModel):
    model: ModelDescriptorResponse
    reasons: list[str]


class PlanRequest(BaseModel):
    firm_id: str
    task_description: str


class PlannedStepResponse(BaseModel):
    name: str
    kind: str
    decision: RoutingDecisionResponse | None


class ExecutionPlanResponse(BaseModel):
    task_description: str
    steps: list[PlannedStepResponse]


class CompareRequest(BaseModel):
    prompt: str
    responses: dict[str, str]


class ResponseMetricsPayload(BaseModel):
    length_words: int
    citation_count: int
    coherence_score: float
    contradiction_flags: list[str]


class ComparisonEntryResponse(BaseModel):
    model_name: str
    metrics: ResponseMetricsPayload
    coverage_score: float
    prompt_compliance_score: float
    overall_score: float


class ComparisonResultResponse(BaseModel):
    prompt: str
    entries: list[ComparisonEntryResponse]
    ranked_model_names: list[str]


class CritiqueRequest(BaseModel):
    model_name: str
    response_text: str


class CriticVerdictResponse(BaseModel):
    model_name: str
    metrics: ResponseMetricsPayload
    quality_score: float
    issues: list[str]


class ModelPositionPayload(BaseModel):
    model_name: str
    text: str
    quality_score: float = 0.5


class ConsensusRequest(BaseModel):
    topic: str
    positions: list[ModelPositionPayload]


class ConsensusOutcomeResponse(BaseModel):
    topic: str
    agreement_ratio: float
    synthesis: str
    divergences: list[str]


class FuseRequest(BaseModel):
    positions: list[ModelPositionPayload]


class FusionSourceResponse(BaseModel):
    model_name: str
    text: str
    citation_count: int


class FusedResponsePayload(BaseModel):
    fused_text: str
    sources: list[FusionSourceResponse]
    provenance: dict[str, str]


class BenchmarkRunRequest(BaseModel):
    model_name: str
    response_text: str
    cost_usd: float
    latency_ms: float


class BenchmarkRunResponse(BaseModel):
    model_name: str
    quality_score: float
    cost_usd: float
    latency_ms: float
    hallucination_flags: int
    token_count: int


class ModelTelemetrySnapshotResponse(BaseModel):
    model_name: str
    availability: bool
    quality_score: float
    average_latency_ms: float
    cost_per_1k_tokens_usd: float
    error_rate: float
    stability_score: float
    average_feedback: float
    total_calls: int
    usage_share: float


class FabricTelemetryResponse(BaseModel):
    models: list[ModelTelemetrySnapshotResponse]
    fallback_rate: float
    cache_hit_rate: float


class CostSummaryResponse(BaseModel):
    firm_id: str
    cache_hit_rate: float
    cost_by_provider: dict[str, float]


class PolicyCreateRequest(BaseModel):
    type: str
    model_name: str
    reason: str
    allowed_countries: list[str] | None = None
    allowed_data_types: list[str] | None = None


class PolicyResponse(BaseModel):
    id: str
    type: str
    model_name: str
    reason: str
    allowed_countries: list[str] | None
    allowed_data_types: list[str] | None
    active: bool


class GovernanceEvaluateRequest(BaseModel):
    firm_id: str
    model_name: str
    country: str | None = None
    data_type: str | None = None


class PolicyDecisionResponse(BaseModel):
    id: str
    firm_id: str
    model_name: str
    allowed: bool
    reasons: list[str]
