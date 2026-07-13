from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission
from tmis.legal_copilot_framework.api.schemas import (
    CopilotActivationRequest,
    CopilotActivationResponse,
    CopilotManifestResponse,
    CopilotMetricsResponse,
    CopilotRegisterRequest,
    DemoSeedRequest,
    DemoSeedResponse,
    DocumentPackPublishRequest,
    KnowledgePackPublishRequest,
    LegalCopilotResponse,
    MarketplacePublishRequest,
    MarketplacePublishResponse,
    PackPublishResponse,
    PromptPackPublishRequest,
    ReasoningPackPublishRequest,
    WorkflowPackPublishRequest,
)
from tmis.legal_copilot_framework.bootstrap import (
    get_copilot_builder,
    get_copilot_engine,
    get_copilot_metrics_engine,
    get_copilot_registry,
    get_document_pack_engine,
    get_knowledge_pack_engine,
    get_prompt_pack_engine,
    get_reasoning_pack_engine,
    get_workflow_pack_engine,
    publish_copilot_to_marketplace,
    seed_demo_copilots_once,
)
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.schemas import CopilotActivation, LegalCopilot
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.metrics.engine import CopilotMetricsEngine
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.reasoning_packs.schemas import ReasoningStrategyType
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.sdk.builder import CopilotBuilder, CopilotValidationError
from tmis.legal_copilot_framework.sdk.schemas import CopilotSpec
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine
from tmis.legal_drafting.templates.schemas import DocumentType

router = APIRouter(prefix="/legal-copilots", tags=["legal-copilot-framework"])
"""Phase 12's "installer, activer, désactiver" collapses to two REST
actions here, not three: `POST /{id}/install` both records the
per-firm `CopilotActivation` and turns it on (`CopilotEngine.
activate`) — a firm never "has" a copilot without it being usable,
mirroring how `platform_sdk.marketplace` install already works for
plugins. Calling `/install` again after `/deactivate` re-activates
it, so no separate `/activate` endpoint is needed. See the Sprint 24
audit report for why per-copilot activation stays its own mechanism
rather than reusing `business_platform.modules.ModuleRegistry`."""


def _copilot_response(copilot: LegalCopilot) -> LegalCopilotResponse:
    return LegalCopilotResponse(
        id=copilot.id,
        name=copilot.name,
        domain=copilot.domain.value,
        description=copilot.description,
        version=copilot.version,
        team_id=copilot.team_id,
        status=copilot.status.value,
        dependencies=copilot.dependencies,
        compatible_models=copilot.compatible_models,
        prompt_pack_id=copilot.prompt_pack_id,
        knowledge_pack_ids=copilot.knowledge_pack_ids,
        reasoning_pack_ids=copilot.reasoning_pack_ids,
        document_pack_ids=copilot.document_pack_ids,
        workflow_pack_ids=copilot.workflow_pack_ids,
        validation_policy_ids=copilot.validation_policy_ids,
        permissions=copilot.permissions,
        metrics_enabled=copilot.metrics_enabled,
        created_at=copilot.created_at.isoformat(),
    )


def _activation_response(activation: CopilotActivation) -> CopilotActivationResponse:
    return CopilotActivationResponse(
        firm_id=activation.firm_id,
        copilot_id=activation.copilot_id,
        active=activation.active,
        updated_at=activation.updated_at.isoformat(),
    )


def _pack_response(
    pack_id: str, name: str, domain: LegalDomain, version: int
) -> PackPublishResponse:
    return PackPublishResponse(id=pack_id, name=name, domain=domain.value, version=version)


def _parse_domain(domain: str) -> LegalDomain:
    try:
        return LegalDomain(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"unknown domain {domain!r}") from exc


# ---------------------------------------------------------------------------
# Copilot lifecycle: enregistrer, installer, désactiver, versionner
# ---------------------------------------------------------------------------


@router.post("/register", response_model=LegalCopilotResponse)
def register_copilot(
    payload: CopilotRegisterRequest,
    builder: CopilotBuilder = Depends(get_copilot_builder),
) -> LegalCopilotResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    spec = CopilotSpec(
        id=payload.id,
        name=payload.name,
        domain=_parse_domain(payload.domain),
        description=payload.description,
        version=payload.version,
        author=payload.author,
        compatibility=payload.compatibility,
        dependencies=payload.dependencies,
        agent_ids=payload.agent_ids,
        compatible_models=payload.compatible_models,
        workflow_pack_ids=payload.workflow_pack_ids,
        document_pack_ids=payload.document_pack_ids,
        knowledge_pack_ids=payload.knowledge_pack_ids,
        reasoning_pack_ids=payload.reasoning_pack_ids,
        prompt_pack_id=payload.prompt_pack_id,
        validation_policy_ids=payload.validation_policy_ids,
        permissions=payload.permissions,
        metrics_enabled=payload.metrics_enabled,
    )
    try:
        copilot = builder.build(spec)
    except CopilotValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _copilot_response(copilot)


@router.get("", response_model=list[LegalCopilotResponse])
def list_copilots(
    engine: CopilotEngine = Depends(get_copilot_engine),
) -> list[LegalCopilotResponse]:
    return [_copilot_response(c) for c in engine.list_all()]


@router.get("/{copilot_id}", response_model=LegalCopilotResponse)
def get_copilot(
    copilot_id: str, engine: CopilotEngine = Depends(get_copilot_engine)
) -> LegalCopilotResponse:
    try:
        return _copilot_response(engine.get(copilot_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{copilot_id}/versions", response_model=list[CopilotManifestResponse])
def list_copilot_versions(
    copilot_id: str, registry: CopilotRegistry = Depends(get_copilot_registry)
) -> list[CopilotManifestResponse]:
    versions = registry.list_versions(copilot_id)
    if not versions:
        raise HTTPException(status_code=404, detail=copilot_id)
    return [
        CopilotManifestResponse(
            copilot_id=manifest.copilot_id,
            version=manifest.version,
            domain=manifest.domain.value,
            author=manifest.author,
            status=manifest.status.value,
            dependencies=manifest.dependencies,
            compatibility=manifest.compatibility,
            published_at=manifest.published_at.isoformat(),
        )
        for manifest in versions
    ]


@router.post("/{copilot_id}/install", response_model=CopilotActivationResponse)
def install_copilot(
    copilot_id: str,
    payload: CopilotActivationRequest,
    engine: CopilotEngine = Depends(get_copilot_engine),
) -> CopilotActivationResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    try:
        activation = engine.activate(payload.firm_id, copilot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _activation_response(activation)


@router.post("/{copilot_id}/deactivate", response_model=CopilotActivationResponse)
def deactivate_copilot(
    copilot_id: str,
    payload: CopilotActivationRequest,
    engine: CopilotEngine = Depends(get_copilot_engine),
) -> CopilotActivationResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    activation = engine.deactivate(payload.firm_id, copilot_id)
    return _activation_response(activation)


# ---------------------------------------------------------------------------
# Publier un pack
# ---------------------------------------------------------------------------


@router.post("/packs/prompt", response_model=PackPublishResponse)
def publish_prompt_pack(
    payload: PromptPackPublishRequest,
    engine: PromptPackEngine = Depends(get_prompt_pack_engine),
) -> PackPublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    pack = engine.register_pack(
        payload.id,
        payload.name,
        _parse_domain(payload.domain),
        system_prompt_ids=payload.system_prompt_ids,
        business_prompt_ids=payload.business_prompt_ids,
        parent_pack_id=payload.parent_pack_id,
        overrides=payload.overrides,
    )
    return _pack_response(pack.id, pack.name, pack.domain, pack.version)


@router.post("/packs/knowledge", response_model=PackPublishResponse)
def publish_knowledge_pack(
    payload: KnowledgePackPublishRequest,
    engine: KnowledgePackEngine = Depends(get_knowledge_pack_engine),
) -> PackPublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    pack = engine.register_pack(
        payload.id,
        payload.name,
        _parse_domain(payload.domain),
        taxonomy_root_id=payload.taxonomy_root_id,
        source_refs=payload.source_refs,
        update_rules=payload.update_rules,
        quality_controls=payload.quality_controls,
        knowledge_object_ids=payload.knowledge_object_ids,
    )
    return _pack_response(pack.id, pack.name, pack.domain, pack.version)


@router.post("/packs/reasoning", response_model=PackPublishResponse)
def publish_reasoning_pack(
    payload: ReasoningPackPublishRequest,
    engine: ReasoningPackEngine = Depends(get_reasoning_pack_engine),
) -> PackPublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    try:
        strategy_types = frozenset(ReasoningStrategyType(s) for s in payload.strategy_types)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    pack = engine.register_pack(
        payload.id,
        payload.name,
        _parse_domain(payload.domain),
        strategy_types,
        pattern_ids=payload.pattern_ids,
    )
    return _pack_response(pack.id, pack.name, pack.domain, pack.version)


@router.post("/packs/document", response_model=PackPublishResponse)
def publish_document_pack(
    payload: DocumentPackPublishRequest,
    engine: DocumentPackEngine = Depends(get_document_pack_engine),
) -> PackPublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    try:
        document_types = tuple(DocumentType(d) for d in payload.document_types)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    pack = engine.register_pack(
        payload.id,
        payload.name,
        _parse_domain(payload.domain),
        document_types=document_types,
        cabinet_template_ids=payload.cabinet_template_ids,
        validations=payload.validations,
        quality_controls=payload.quality_controls,
    )
    return _pack_response(pack.id, pack.name, pack.domain, pack.version)


@router.post("/packs/workflow", response_model=PackPublishResponse)
def publish_workflow_pack(
    payload: WorkflowPackPublishRequest,
    engine: WorkflowPackEngine = Depends(get_workflow_pack_engine),
) -> PackPublishResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    pack = engine.register_pack(
        payload.id,
        payload.name,
        _parse_domain(payload.domain),
        workflow_template_ids=payload.workflow_template_ids,
    )
    return _pack_response(pack.id, pack.name, pack.domain, pack.version)


# ---------------------------------------------------------------------------
# Consulter les métriques
# ---------------------------------------------------------------------------


@router.get("/{copilot_id}/metrics", response_model=CopilotMetricsResponse)
def get_copilot_metrics(
    copilot_id: str,
    firm_id: str,
    user_id: str,
    metrics: CopilotMetricsEngine = Depends(get_copilot_metrics_engine),
) -> CopilotMetricsResponse:
    authorize_or_403(firm_id, user_id, Permission.COPILOT_MANAGE)
    snapshot = metrics.snapshot(copilot_id, firm_id=firm_id)
    return CopilotMetricsResponse(
        copilot_id=snapshot.copilot_id,
        usage_count=snapshot.usage_count,
        total_ai_cost_usd=snapshot.total_ai_cost_usd,
        avg_response_time_ms=snapshot.avg_response_time_ms,
        validation_rate=snapshot.validation_rate,
        pack_reuse_count=snapshot.pack_reuse_count,
        satisfaction_score=snapshot.satisfaction_score,
    )


# ---------------------------------------------------------------------------
# Demo copilots (Phase 12) — fictional data, seeded once per process
# ---------------------------------------------------------------------------


@router.post("/demo/seed", response_model=DemoSeedResponse)
def seed_demo(payload: DemoSeedRequest) -> DemoSeedResponse:
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    return DemoSeedResponse(copilot_ids=seed_demo_copilots_once())


# ---------------------------------------------------------------------------
# Marketplace preparation (Phase 12's "Marketplace" section)
# ---------------------------------------------------------------------------


@router.post("/{copilot_id}/publish-to-marketplace", response_model=MarketplacePublishResponse)
def publish_to_marketplace(
    copilot_id: str, payload: MarketplacePublishRequest
) -> MarketplacePublishResponse:
    """Runs the copilot through the existing `platform_sdk` publishing
    pipeline so it becomes a searchable, installable
    `platform_sdk.marketplace` listing — no second marketplace."""
    authorize_or_403(payload.firm_id, payload.user_id, Permission.COPILOT_MANAGE)
    try:
        plugin_manifest = publish_copilot_to_marketplace(copilot_id, payload.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MarketplacePublishResponse(
        plugin_id=plugin_manifest.id,
        plugin_type=plugin_manifest.plugin_type.value,
        version=plugin_manifest.version,
        status=plugin_manifest.status.value,
        signature=plugin_manifest.signature,
    )
