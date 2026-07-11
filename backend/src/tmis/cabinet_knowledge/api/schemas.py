from datetime import datetime
from typing import Any

from pydantic import BaseModel


class KnowledgeObjectResponse(BaseModel):
    id: str
    firm_id: str
    type: str
    title: str
    content: dict[str, Any]
    author: str
    created_at: datetime
    updated_at: datetime
    version: int
    status: str
    quality_score: float
    tags: list[str]
    is_published: bool
    usage_count: int


class KnowledgeCreateRequest(BaseModel):
    firm_id: str
    type: str
    title: str
    content: dict[str, Any]
    author: str
    tags: list[str] = []


class PlaybookStepIn(BaseModel):
    order: int
    title: str
    description: str
    documents: list[str] = []
    risks: list[str] = []
    vigilance_points: list[str] = []


class PlaybookStepOut(BaseModel):
    order: int
    title: str
    description: str
    documents: list[str]
    risks: list[str]
    vigilance_points: list[str]


class PlaybookCreateRequest(BaseModel):
    firm_id: str
    title: str
    case_type: str
    steps: list[PlaybookStepIn]
    checklist: list[str] = []
    author: str


class PlaybookResponse(BaseModel):
    id: str
    case_type: str
    title: str
    steps: list[PlaybookStepOut]
    checklist: list[str]


class PlaybookInstanceStartRequest(BaseModel):
    firm_id: str
    case_reference: str | None = None


class PlaybookInstanceResponse(BaseModel):
    id: str
    firm_id: str
    playbook_id: str
    case_reference: str | None
    completed_step_orders: list[int]
    progress: float
    completed: bool


class ClauseVariantIn(BaseModel):
    id: str
    text: str
    notes: str = ""
    language: str = "fr"


class ClauseVariantOut(BaseModel):
    id: str
    text: str
    notes: str
    language: str


class ClauseCreateRequest(BaseModel):
    firm_id: str
    title: str
    domain: str
    clause_type: str
    variants: list[ClauseVariantIn]
    author: str
    comments: list[str] = []
    jurisprudence_refs: list[str] = []


class ClauseResponse(BaseModel):
    id: str
    domain: str
    clause_type: str
    title: str
    variants: list[ClauseVariantOut]
    comments: list[str]
    jurisprudence_refs: list[str]


class TemplateCreateRequest(BaseModel):
    firm_id: str
    title: str
    document_type: str
    structure: list[str]
    author: str
    body_variables: list[str] = []


class TemplateResponse(BaseModel):
    id: str
    document_type: str
    title: str
    structure: list[str]
    body_variables: list[str]


class ReasoningPatternCreateRequest(BaseModel):
    firm_id: str
    title: str
    context: str
    strategy: str
    arguments: list[str]
    author: str
    counter_arguments: list[str] = []
    references: list[str] = []
    confidence_level: float = 0.5


class ReasoningPatternResponse(BaseModel):
    id: str
    title: str
    context: str
    strategy: str
    arguments: list[str]
    counter_arguments: list[str]
    references: list[str]
    confidence_level: float


class WritingStyleUpdateRequest(BaseModel):
    firm_id: str
    actor: str
    vocabulary: list[str] | None = None
    favorite_expressions: list[str] | None = None
    structure_preferences: list[str] | None = None
    signature_block: str | None = None


class WritingStyleResponse(BaseModel):
    id: str
    vocabulary: list[str]
    favorite_expressions: list[str]
    structure_preferences: list[str]
    signature_block: str


class BestPracticeCreateRequest(BaseModel):
    firm_id: str
    title: str
    description: str
    domain: str
    source: str
    author: str
    applicability: list[str] = []


class BestPracticeResponse(BaseModel):
    id: str
    title: str
    description: str
    domain: str
    source: str
    applicability: list[str]


class LessonLearnedCreateRequest(BaseModel):
    firm_id: str
    title: str
    context: str
    outcome: str
    recommendation: str
    author: str
    related_case_reference: str | None = None


class LessonLearnedResponse(BaseModel):
    id: str
    title: str
    context: str
    outcome: str
    recommendation: str
    related_case_reference: str | None


class FeedbackSubmitRequest(BaseModel):
    firm_id: str
    knowledge_object_id: str
    action: str
    author: str
    comment: str = ""


class FeedbackResponse(BaseModel):
    id: str
    knowledge_object_id: str
    action: str
    author: str
    comment: str
    created_at: datetime


class SubmitForValidationRequest(BaseModel):
    firm_id: str
    requested_by: str


class ValidationDecisionRequest(BaseModel):
    firm_id: str
    decision: str
    reviewer: str
    comment: str | None = None


class ValidationRequestResponse(BaseModel):
    id: str
    firm_id: str
    knowledge_object_id: str
    requested_by: str
    status: str
    reviewer: str | None
    comment: str | None


class GovernanceEventResponse(BaseModel):
    id: str
    from_status: str
    to_status: str
    actor: str
    reason: str | None
    created_at: datetime


class ApprovalPublishRequest(BaseModel):
    firm_id: str
    approver: str


class LineageResponse(BaseModel):
    knowledge_object_id: str
    current_version: int
    origin_source_refs: list[list[str]]
    governance_events: list[GovernanceEventResponse]


class SearchRequest(BaseModel):
    firm_id: str
    type: str | None = None
    status: str | None = None
    tag: str | None = None
    keyword: str | None = None
    published_only: bool = False


class RecommendationRequest(BaseModel):
    firm_id: str
    domain_tag: str | None = None
    keywords: list[str] = []
    limit: int = 5


class RecommendationResponse(BaseModel):
    knowledge_object_id: str
    object_type: str
    title: str
    score: float
    explanation: str


class EvaluationResponse(BaseModel):
    firm_id: str
    total_objects: int
    by_status: dict[str, int]
    validation_rate: float
    average_quality_score: float
    most_reused: list[str]
    feedback_acceptance_rate: float
