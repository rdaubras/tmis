from fastapi import APIRouter, HTTPException

from tmis.cabinet_knowledge.bootstrap import get_validation_engine
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission
from tmis.legal_knowledge_graph.api.schemas import (
    AccessPolicyRequest,
    AccessPolicyResponse,
    AnalyticsResponse,
    FeedbackRequest,
    FeedbackResponse,
    IngestRequest,
    IngestResponse,
    NodeResponse,
    PublishRequest,
    PublishResponse,
    QualityResponse,
    RelationResponse,
    ResolutionDecisionRequest,
    ResolutionMatchResponse,
    ResolutionProposeRequest,
    SearchResponse,
    ValidationDecisionRequest,
    ValidationDecisionResponse,
)
from tmis.legal_knowledge_graph.bootstrap import (
    get_entity_resolution_engine,
    get_graph_access_policy_engine,
    get_graph_analytics_engine,
    get_graph_engine,
    get_graph_feedback_engine,
    get_graph_quality_engine,
    get_ingestion_pipeline,
    get_semantic_engine,
)
from tmis.legal_knowledge_graph.entity_resolution.schemas import ResolutionMatch
from tmis.legal_knowledge_graph.human_validation.schemas import FeedbackAction
from tmis.legal_knowledge_graph.ingestion.schemas import IngestionSourceType

router = APIRouter(prefix="/legal-knowledge-graph", tags=["legal-knowledge-graph"])
"""REST surface for the Sprint 25 Legal Knowledge Graph & Semantic
Intelligence Platform. Every handler is a thin wrapper over an engine
built in `legal_knowledge_graph`'s own modules — no business logic
lives here, exactly like every other bounded context's `api/routes.py`
in this codebase. Every mutating and read action is gated by
`identity_platform.api.guard.authorize_or_403` with the sprint's own
`Permission.KNOWLEDGE_GRAPH_MANAGE`, per the "respecter l'Identity
Platform" constraint."""


def _validation_decision(value: str) -> ValidationDecision:
    try:
        return ValidationDecision(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"unknown decision {value!r}") from exc


def _source_type(value: str) -> IngestionSourceType:
    try:
        return IngestionSourceType(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"unknown source_type {value!r}") from exc


def _feedback_action(value: str) -> FeedbackAction:
    try:
        return FeedbackAction(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"unknown action {value!r}") from exc


# ---------------------------------------------------------------------------
# Phase 5 — Knowledge Ingestion Pipeline: add a knowledge item, publish
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=IngestResponse)
async def ingest(payload: IngestRequest) -> IngestResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    result = await get_ingestion_pipeline().ingest(
        payload.firm_id,
        _source_type(payload.source_type),
        payload.title,
        payload.content_text,
        payload.author,
        source_refs=payload.source_refs,
    )
    return IngestResponse(
        knowledge_object_id=result.knowledge_object_id,
        graph_node_id=result.graph_node_id,
        extracted_entity_labels=result.extracted_entity_labels,
        classification_category=result.classification_category,
        classification_confidence=result.classification_confidence,
        validation_request_id=result.validation_request_id,
    )


@router.post("/publish", response_model=PublishResponse)
def publish(payload: PublishRequest) -> PublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    obj = get_ingestion_pipeline().publish(
        payload.firm_id, payload.knowledge_object_id, payload.approver
    )
    return PublishResponse(id=obj.id, status=obj.status.value)


@router.post("/validation/{request_id}/decide", response_model=ValidationDecisionResponse)
def decide_validation(
    request_id: str, payload: ValidationDecisionRequest
) -> ValidationDecisionResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    try:
        request = get_validation_engine().decide(
            payload.firm_id,
            request_id,
            _validation_decision(payload.decision),
            payload.reviewer,
            payload.comment,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="validation request not found") from exc
    return ValidationDecisionResponse(id=request.id, status=request.status.value)


# ---------------------------------------------------------------------------
# Phase 3 — Semantic Engine: search the graph
# ---------------------------------------------------------------------------


@router.get("/search", response_model=list[SearchResponse])
async def search(firm_id: str, user_id: str, query: str, top_k: int = 5) -> list[SearchResponse]:
    authorize_or_403(firm_id, user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    matches = await get_semantic_engine().search_by_intent(firm_id, query, top_k)
    return [SearchResponse(node_id=m.node_id, score=m.score) for m in matches]


# ---------------------------------------------------------------------------
# Phase 2 — Knowledge Graph Core: consult a node's relations/neighbors
# ---------------------------------------------------------------------------


@router.get("/nodes/{node_id}/relations", response_model=list[RelationResponse])
def node_relations(node_id: str, firm_id: str, user_id: str) -> list[RelationResponse]:
    authorize_or_403(firm_id, user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    relations = get_graph_engine().relations_for(firm_id, node_id)
    return [
        RelationResponse(
            id=r.id,
            source_id=r.source_id,
            target_id=r.target_id,
            relation_type=r.relation_type.value,
            explanation=r.explanation,
            confidence=r.confidence,
        )
        for r in relations
    ]


@router.get("/nodes/{node_id}/neighbors", response_model=list[NodeResponse])
def node_neighbors(node_id: str, firm_id: str, user_id: str) -> list[NodeResponse]:
    authorize_or_403(firm_id, user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    graph = get_graph_engine()
    try:
        graph.get_node(firm_id, node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="node not found") from exc
    return [
        NodeResponse(id=n.id, node_type=n.node_type.value, ref_id=n.ref_id, label=n.label)
        for n in graph.neighbors(firm_id, node_id)
    ]


# ---------------------------------------------------------------------------
# Phase 6 — Human Validation Loop: annotate
# ---------------------------------------------------------------------------


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    feedback = get_graph_feedback_engine().submit(
        payload.firm_id,
        payload.subject_id,
        _feedback_action(payload.action),
        payload.author,
        payload.comment,
    )
    return FeedbackResponse(
        id=feedback.id,
        subject_id=feedback.subject_id,
        action=feedback.action.value,
        author=feedback.author,
        comment=feedback.comment,
    )


# ---------------------------------------------------------------------------
# Phase 4 — Entity Resolution
# ---------------------------------------------------------------------------


def _resolution_response(match: ResolutionMatch) -> ResolutionMatchResponse:
    return ResolutionMatchResponse(
        id=match.id,
        node_id_a=match.node_id_a,
        node_id_b=match.node_id_b,
        score=match.score,
        status=match.status.value,
        decided_by=match.decided_by,
    )


@router.post("/entity-resolution/propose", response_model=ResolutionMatchResponse)
async def propose_resolution(payload: ResolutionProposeRequest) -> ResolutionMatchResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    match = await get_entity_resolution_engine().propose_match(
        payload.firm_id, payload.node_id_a, payload.node_id_b
    )
    return _resolution_response(match)


@router.post("/entity-resolution/{match_id}/confirm", response_model=ResolutionMatchResponse)
def confirm_resolution(
    match_id: str, payload: ResolutionDecisionRequest
) -> ResolutionMatchResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    try:
        match = get_entity_resolution_engine().confirm(payload.firm_id, match_id, payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="resolution match not found") from exc
    return _resolution_response(match)


@router.post("/entity-resolution/{match_id}/reject", response_model=ResolutionMatchResponse)
def reject_resolution(
    match_id: str, payload: ResolutionDecisionRequest
) -> ResolutionMatchResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    try:
        match = get_entity_resolution_engine().reject(payload.firm_id, match_id, payload.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="resolution match not found") from exc
    return _resolution_response(match)


# ---------------------------------------------------------------------------
# Phase 8 — Knowledge Governance
# ---------------------------------------------------------------------------


@router.post("/nodes/{node_id}/policy", response_model=AccessPolicyResponse)
def set_access_policy(node_id: str, payload: AccessPolicyRequest) -> AccessPolicyResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    policy = get_graph_access_policy_engine().set_policy(
        payload.firm_id,
        node_id,
        confidentiality_level=payload.confidentiality_level,
        retention_days=payload.retention_days,
    )
    return AccessPolicyResponse(
        id=policy.id,
        node_id=policy.node_id,
        confidentiality_level=policy.confidentiality_level,
        retention_days=policy.retention_days,
    )


# ---------------------------------------------------------------------------
# Phase 9 — Knowledge Quality Engine
# ---------------------------------------------------------------------------


@router.get("/nodes/{node_id}/quality", response_model=QualityResponse)
def node_quality(node_id: str, firm_id: str, user_id: str) -> QualityResponse:
    authorize_or_403(firm_id, user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    try:
        breakdown = get_graph_quality_engine().evaluate(firm_id, node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="node not found") from exc
    return QualityResponse(
        node_id=breakdown.node_id,
        duplicate_count=breakdown.duplicate_count,
        contradiction_count=breakdown.contradiction_count,
        missing_sources=breakdown.missing_sources,
        confidence=breakdown.confidence,
    )


# ---------------------------------------------------------------------------
# Phase 10 — Knowledge Analytics
# ---------------------------------------------------------------------------


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(firm_id: str, user_id: str) -> AnalyticsResponse:
    authorize_or_403(firm_id, user_id, Permission.KNOWLEDGE_GRAPH_MANAGE)
    snapshot = get_graph_analytics_engine().snapshot(firm_id)
    return AnalyticsResponse(
        node_count=snapshot.node_count,
        avg_search_latency_ms=snapshot.avg_search_latency_ms,
        unresolved_search_count=snapshot.unresolved_search_count,
        human_validation_count=snapshot.human_validation_count,
        enrichment_count=snapshot.enrichment_count,
        avg_answer_quality=snapshot.avg_answer_quality,
    )
