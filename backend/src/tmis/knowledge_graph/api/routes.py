from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.ai_governance.policy_engine.schemas import PolicyEvaluation
from tmis.knowledge_graph.analytics.engine import KnowledgeGraphAnalytics
from tmis.knowledge_graph.api.schemas import (
    AnalyticsSnapshotResponse,
    AttachFederatedRelationsRequest,
    AttachResolvedEntitiesRequest,
    CrossScopeQueryRequest,
    DecideResolutionRequest,
    EntityOccurrenceRequest,
    EvaluateEntityVisibilityRequest,
    FederatedNeighborhoodResponse,
    FederatedNodeRefResponse,
    GovernancePolicyResponse,
    KnowledgePackFederationResponse,
    PolicyEvaluationResponse,
    ResolvedEntityResponse,
    ResolveEntityRequest,
    RestrictEntityVisibilityRequest,
    SemanticLinkRequest,
    SemanticLinkResponse,
)
from tmis.knowledge_graph.bootstrap import (
    get_copilot_knowledge_bridge,
    get_entity_resolution_engine,
    get_federation_query_engine,
    get_knowledge_graph_analytics,
    get_knowledge_graph_governance,
    get_semantic_link_engine,
)
from tmis.knowledge_graph.copilot_bridge.engine import CopilotKnowledgeBridge
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import EntityOccurrence, ResolvedEntity
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import FederatedNeighborhood, GraphOrigin
from tmis.knowledge_graph.governance.engine import KnowledgeGraphGovernance
from tmis.knowledge_graph.semantic_intelligence.engine import SemanticLinkEngine
from tmis.legal_copilot_framework.knowledge_packs.schemas import KnowledgePack

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


def _neighborhood_response(neighborhood: FederatedNeighborhood) -> FederatedNeighborhoodResponse:
    return FederatedNeighborhoodResponse(
        subject=FederatedNodeRefResponse(
            origin=neighborhood.subject.origin.value,
            node_id=neighborhood.subject.node_id,
            label=neighborhood.subject.label,
            node_type=neighborhood.subject.node_type,
        ),
        neighbors=[
            FederatedNodeRefResponse(
                origin=n.origin.value, node_id=n.node_id, label=n.label, node_type=n.node_type
            )
            for n in neighborhood.neighbors
        ],
    )


def _resolved_entity_response(entity: ResolvedEntity) -> ResolvedEntityResponse:
    return ResolvedEntityResponse(
        id=entity.id,
        firm_id=entity.firm_id,
        occurrences=[
            EntityOccurrenceRequest(origin=o.origin.value, node_id=o.node_id, label=o.label)
            for o in entity.occurrences
        ],
        confidence=entity.confidence,
        status=entity.status.value,
        validation_request_id=entity.validation_request_id,
    )


def _policy_evaluation_response(evaluation: PolicyEvaluation) -> PolicyEvaluationResponse:
    return PolicyEvaluationResponse(
        id=evaluation.id,
        firm_id=evaluation.firm_id,
        production_id=evaluation.production_id,
        allowed=evaluation.allowed,
        reasons=evaluation.reasons,
    )


@router.post("/federation/cross-scope", response_model=list[FederatedNeighborhoodResponse])
def cross_scope_query(
    request: CrossScopeQueryRequest,
    federation: FederationQueryEngine = Depends(get_federation_query_engine),
) -> list[FederatedNeighborhoodResponse]:
    occurrences = [(GraphOrigin(origin), node_id) for origin, node_id in request.occurrences]
    results = federation.cross_scope_neighborhood(request.firm_id, occurrences)
    return [_neighborhood_response(r) for r in results]


@router.post("/entity-resolution/resolve", response_model=ResolvedEntityResponse)
def resolve_entity(
    request: ResolveEntityRequest,
    engine: EntityResolutionEngine = Depends(get_entity_resolution_engine),
) -> ResolvedEntityResponse:
    occurrences = [
        EntityOccurrence(origin=GraphOrigin(o.origin), node_id=o.node_id, label=o.label)
        for o in request.occurrences
    ]
    resolved = engine.resolve(
        request.firm_id, request.requested_by, occurrences, request.approver_ids
    )
    return _resolved_entity_response(resolved)


@router.post("/entity-resolution/{entity_id}/decide", response_model=ResolvedEntityResponse)
def decide_entity_resolution(
    entity_id: str,
    request: DecideResolutionRequest,
    engine: EntityResolutionEngine = Depends(get_entity_resolution_engine),
) -> ResolvedEntityResponse:
    try:
        updated = engine.decide(
            request.firm_id,
            entity_id,
            request.approver_id,
            ValidationDecisionType(request.decision),
        )
    except KeyError as exc:
        detail = f"resolved entity {entity_id!r} not found"
        raise HTTPException(status_code=404, detail=detail) from exc
    return _resolved_entity_response(updated)


@router.get("/entity-resolution/{entity_id}", response_model=ResolvedEntityResponse)
def get_resolved_entity(
    entity_id: str,
    firm_id: str,
    engine: EntityResolutionEngine = Depends(get_entity_resolution_engine),
) -> ResolvedEntityResponse:
    entity = engine.get(firm_id, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"resolved entity {entity_id!r} not found")
    return _resolved_entity_response(entity)


@router.get("/entity-resolution", response_model=list[ResolvedEntityResponse])
def list_resolved_entities(
    firm_id: str, engine: EntityResolutionEngine = Depends(get_entity_resolution_engine)
) -> list[ResolvedEntityResponse]:
    return [_resolved_entity_response(e) for e in engine.list_for_firm(firm_id)]


@router.post("/semantic-intelligence/link", response_model=list[SemanticLinkResponse])
async def link_semantic_objects(
    request: SemanticLinkRequest,
    engine: SemanticLinkEngine = Depends(get_semantic_link_engine),
) -> list[SemanticLinkResponse]:
    links = await engine.link_objects(request.objects)
    return [
        SemanticLinkResponse(
            id=link.id,
            source_id=link.source_id,
            target_id=link.target_id,
            score=link.score,
            embedding_name=link.embedding_name,
        )
        for link in links
    ]


@router.get("/semantic-intelligence/{object_id}", response_model=list[SemanticLinkResponse])
def get_semantic_links(
    object_id: str, engine: SemanticLinkEngine = Depends(get_semantic_link_engine)
) -> list[SemanticLinkResponse]:
    return [
        SemanticLinkResponse(
            id=link.id,
            source_id=link.source_id,
            target_id=link.target_id,
            score=link.score,
            embedding_name=link.embedding_name,
        )
        for link in engine.links_for(object_id)
    ]


@router.get("/analytics/{firm_id}/snapshot", response_model=AnalyticsSnapshotResponse)
def analytics_snapshot(
    firm_id: str, analytics: KnowledgeGraphAnalytics = Depends(get_knowledge_graph_analytics)
) -> AnalyticsSnapshotResponse:
    snapshot = analytics.snapshot(firm_id)
    return AnalyticsSnapshotResponse(firm_id=firm_id, **snapshot)


@router.post("/governance/restrict-entity-visibility", response_model=GovernancePolicyResponse)
def restrict_entity_visibility(
    request: RestrictEntityVisibilityRequest,
    governance: KnowledgeGraphGovernance = Depends(get_knowledge_graph_governance),
) -> GovernancePolicyResponse:
    policy = governance.restrict_entity_visibility(
        request.firm_id, request.entity_id, request.required_role, request.reason
    )
    return GovernancePolicyResponse(
        id=policy.id,
        firm_id=policy.firm_id,
        type=policy.type.value,
        reason=policy.reason,
        required_role=policy.required_role,
        restricted_entity_id=policy.restricted_entity_id,
        active=policy.active,
    )


@router.post("/governance/evaluate-entity-visibility", response_model=PolicyEvaluationResponse)
def evaluate_entity_visibility(
    request: EvaluateEntityVisibilityRequest,
    governance: KnowledgeGraphGovernance = Depends(get_knowledge_graph_governance),
) -> PolicyEvaluationResponse:
    evaluation = governance.evaluate_entity_visibility(
        request.firm_id, request.production_id, request.entity_id, request.user_role
    )
    return _policy_evaluation_response(evaluation)


def _pack_response(pack: KnowledgePack) -> KnowledgePackFederationResponse:
    return KnowledgePackFederationResponse(
        id=pack.id,
        version=pack.version,
        resolved_entity_ids=pack.resolved_entity_ids,
        federated_relation_refs=pack.federated_relation_refs,
    )


@router.post(
    "/copilot-bridge/{pack_id}/attach-entities", response_model=KnowledgePackFederationResponse
)
def attach_resolved_entities(
    pack_id: str,
    request: AttachResolvedEntitiesRequest,
    bridge: CopilotKnowledgeBridge = Depends(get_copilot_knowledge_bridge),
) -> KnowledgePackFederationResponse:
    pack = bridge.attach_resolved_entities(request.firm_id, pack_id, request.entity_ids)
    return _pack_response(pack)


@router.post(
    "/copilot-bridge/{pack_id}/attach-relations", response_model=KnowledgePackFederationResponse
)
def attach_federated_relations(
    pack_id: str,
    request: AttachFederatedRelationsRequest,
    bridge: CopilotKnowledgeBridge = Depends(get_copilot_knowledge_bridge),
) -> KnowledgePackFederationResponse:
    occurrences = [(GraphOrigin(origin), node_id) for origin, node_id in request.occurrences]
    pack = bridge.attach_federated_relations(request.firm_id, pack_id, occurrences)
    return _pack_response(pack)


@router.get(
    "/copilot-bridge/{pack_id}/relations", response_model=list[FederatedNeighborhoodResponse]
)
def resolve_federated_relations(
    pack_id: str,
    firm_id: str,
    bridge: CopilotKnowledgeBridge = Depends(get_copilot_knowledge_bridge),
) -> list[FederatedNeighborhoodResponse]:
    neighborhoods = bridge.resolve_federated_relations(firm_id, pack_id)
    return [_neighborhood_response(n) for n in neighborhoods]
