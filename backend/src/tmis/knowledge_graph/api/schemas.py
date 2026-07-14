from pydantic import BaseModel


class FederatedNodeRefResponse(BaseModel):
    origin: str
    node_id: str
    label: str
    node_type: str


class FederatedNeighborhoodResponse(BaseModel):
    subject: FederatedNodeRefResponse
    neighbors: list[FederatedNodeRefResponse]


class CrossScopeQueryRequest(BaseModel):
    firm_id: str
    occurrences: list[tuple[str, str]]


class EntityOccurrenceRequest(BaseModel):
    origin: str
    node_id: str
    label: str


class ResolveEntityRequest(BaseModel):
    firm_id: str
    requested_by: str
    occurrences: list[EntityOccurrenceRequest]
    approver_ids: tuple[str, ...] = ()


class ResolvedEntityResponse(BaseModel):
    id: str
    firm_id: str
    occurrences: list[EntityOccurrenceRequest]
    confidence: float
    status: str
    validation_request_id: str | None


class DecideResolutionRequest(BaseModel):
    firm_id: str
    approver_id: str
    decision: str


class SemanticLinkRequest(BaseModel):
    objects: list[tuple[str, str]]
    similarity_threshold: float | None = None


class SemanticLinkResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    score: float
    embedding_name: str


class AnalyticsSnapshotResponse(BaseModel):
    firm_id: str
    graph_coverage: float
    entity_resolution_rate: float
    semantic_link_density: float


class RestrictEntityVisibilityRequest(BaseModel):
    firm_id: str
    entity_id: str
    required_role: str
    reason: str


class GovernancePolicyResponse(BaseModel):
    id: str
    firm_id: str
    type: str
    reason: str
    required_role: str | None
    restricted_entity_id: str | None
    active: bool


class EvaluateEntityVisibilityRequest(BaseModel):
    firm_id: str
    production_id: str
    entity_id: str
    user_role: str | None = None


class PolicyEvaluationResponse(BaseModel):
    id: str
    firm_id: str
    production_id: str
    allowed: bool
    reasons: tuple[str, ...]


class AttachResolvedEntitiesRequest(BaseModel):
    firm_id: str
    entity_ids: list[str]


class AttachFederatedRelationsRequest(BaseModel):
    firm_id: str
    occurrences: list[tuple[str, str]]


class KnowledgePackFederationResponse(BaseModel):
    id: str
    version: int
    resolved_entity_ids: tuple[str, ...]
    federated_relation_refs: tuple[str, ...]
