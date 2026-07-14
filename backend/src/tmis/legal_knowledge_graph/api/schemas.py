from pydantic import BaseModel


class IngestRequest(BaseModel):
    firm_id: str
    user_id: str
    source_type: str
    title: str
    content_text: str
    author: str
    source_refs: tuple[str, ...] = ()


class IngestResponse(BaseModel):
    knowledge_object_id: str
    graph_node_id: str
    extracted_entity_labels: tuple[str, ...]
    classification_category: str
    classification_confidence: float
    validation_request_id: str


class PublishRequest(BaseModel):
    firm_id: str
    user_id: str
    knowledge_object_id: str
    approver: str


class PublishResponse(BaseModel):
    id: str
    status: str


class ValidationDecisionRequest(BaseModel):
    firm_id: str
    user_id: str
    decision: str
    reviewer: str
    comment: str | None = None


class ValidationDecisionResponse(BaseModel):
    id: str
    status: str


class SearchResponse(BaseModel):
    node_id: str
    score: float


class RelationResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    explanation: str | None
    confidence: float


class NodeResponse(BaseModel):
    id: str
    node_type: str
    ref_id: str
    label: str


class FeedbackRequest(BaseModel):
    firm_id: str
    user_id: str
    subject_id: str
    action: str
    author: str
    comment: str = ""


class FeedbackResponse(BaseModel):
    id: str
    subject_id: str
    action: str
    author: str
    comment: str


class ResolutionProposeRequest(BaseModel):
    firm_id: str
    user_id: str
    node_id_a: str
    node_id_b: str


class ResolutionDecisionRequest(BaseModel):
    firm_id: str
    user_id: str
    actor: str


class ResolutionMatchResponse(BaseModel):
    id: str
    node_id_a: str
    node_id_b: str
    score: float
    status: str
    decided_by: str | None


class AccessPolicyRequest(BaseModel):
    firm_id: str
    user_id: str
    confidentiality_level: str = "standard"
    retention_days: int | None = None


class AccessPolicyResponse(BaseModel):
    id: str
    node_id: str
    confidentiality_level: str
    retention_days: int | None


class QualityResponse(BaseModel):
    node_id: str
    duplicate_count: int
    contradiction_count: int
    missing_sources: bool
    confidence: float


class AnalyticsResponse(BaseModel):
    node_count: float
    avg_search_latency_ms: float
    unresolved_search_count: int
    human_validation_count: int
    enrichment_count: int
    avg_answer_quality: float
