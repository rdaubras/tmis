from datetime import datetime

from pydantic import BaseModel


class ReasoningRequest(BaseModel):
    question: str
    case_id: str | None = None


class HypothesisResponse(BaseModel):
    id: str
    description: str
    supporting_fact_ids: list[str]
    references: list[str]
    confidence: float
    status: str


class ArgumentResponse(BaseModel):
    id: str
    hypothesis_id: str
    claim: str
    source_connector: str
    source_reference: str
    excerpt: str
    confidence: float


class CounterArgumentResponse(BaseModel):
    id: str
    argument_id: str
    claim: str
    source_connector: str
    source_reference: str
    excerpt: str
    confidence: float


class ConflictResponse(BaseModel):
    id: str
    type: str
    description: str
    explanation: str
    involved_ids: list[str]


class ConfidenceScoreResponse(BaseModel):
    hypothesis_id: str
    value: float
    explanation: str
    factors: dict[str, float]


class StrategyOptionResponse(BaseModel):
    id: str
    hypothesis_id: str
    objective: str
    favorable_points: list[str]
    risks: list[str]
    missing_elements: list[str]


class ExplanationResponse(BaseModel):
    reasoning_steps: list[str]
    components_used: list[str]
    references: list[str]
    hypotheses_considered: list[str]
    limitations: list[str]


class DecisionNodeResponse(BaseModel):
    id: str
    type: str
    label: str


class DecisionEdgeResponse(BaseModel):
    source_id: str
    target_id: str
    relation: str


class DecisionGraphResponse(BaseModel):
    nodes: list[DecisionNodeResponse]
    edges: list[DecisionEdgeResponse]


class ReasoningSessionResponse(BaseModel):
    id: str
    question: str
    case_id: str | None
    hypotheses: list[HypothesisResponse]
    arguments: list[ArgumentResponse]
    counter_arguments: list[CounterArgumentResponse]
    conflicts: list[ConflictResponse]
    confidence_scores: list[ConfidenceScoreResponse]
    strategies: list[StrategyOptionResponse]
    synthesis: str
    explanation: ExplanationResponse | None
    decision_graph: DecisionGraphResponse | None
    duration_ms: float
    created_at: datetime
