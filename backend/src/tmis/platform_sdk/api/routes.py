from fastapi import APIRouter, Depends, HTTPException

from tmis.platform_sdk.api.schemas import (
    ExtensionInstanceResponse,
    InstallRequest,
    MarketplaceListingResponse,
    PluginManifestResponse,
    PortalResourceResponse,
    PublishingActionRequest,
    PublishingEventResponse,
    ReviewRequest,
    ReviewResponse,
)
from tmis.platform_sdk.bootstrap import (
    get_developer_portal_service,
    get_extension_engine,
    get_marketplace_engine,
    get_plugin_registry,
    get_publishing_engine,
)
from tmis.platform_sdk.developer_portal.engine import DeveloperPortalService
from tmis.platform_sdk.developer_portal.schemas import ResourceType
from tmis.platform_sdk.extensions.engine import (
    ExtensionEngine,
    PluginNotAvailableError,
    UngrantablePermissionError,
)
from tmis.platform_sdk.extensions.schemas import ExtensionInstance
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType
from tmis.platform_sdk.publishing.engine import PublishingEngine
from tmis.platform_sdk.publishing.schemas import (
    InvalidPublishingTransitionError,
    ValidationFailedError,
)

router = APIRouter(prefix="/platform-sdk", tags=["platform-sdk"])


def _to_manifest_response(manifest: PluginManifest) -> PluginManifestResponse:
    return PluginManifestResponse(
        id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        plugin_type=manifest.plugin_type.value,
        author=manifest.author,
        description=manifest.description,
        license=manifest.license,
        permissions=sorted(manifest.permissions),
        dependencies=list(manifest.dependencies),
        compatibility=manifest.compatibility,
        status=manifest.status.value,
        signature=manifest.signature,
    )


def _to_extension_response(instance: ExtensionInstance) -> ExtensionInstanceResponse:
    return ExtensionInstanceResponse(
        id=instance.id,
        firm_id=instance.firm_id,
        plugin_id=instance.plugin_id,
        version=instance.version,
        status=instance.status.value,
        granted_permissions=sorted(p.value for p in instance.granted_permissions),
        installed_at=instance.installed_at,
        updated_at=instance.updated_at,
    )


def _get_manifest_or_404(plugin_id: str, registry: InMemoryPluginRegistry) -> PluginManifest:
    manifest = registry.get(plugin_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"plugin {plugin_id} not found")
    return manifest


@router.get("/marketplace", response_model=list[MarketplaceListingResponse])
def search_marketplace(
    query: str | None = None,
    plugin_type: str | None = None,
    marketplace: MarketplaceEngine = Depends(get_marketplace_engine),
) -> list[MarketplaceListingResponse]:
    type_ = PluginType(plugin_type) if plugin_type else None
    listings = marketplace.search(query=query, plugin_type=type_)
    return [
        MarketplaceListingResponse(
            manifest=_to_manifest_response(m),
            average_rating=marketplace.average_rating(m.id),
            review_count=len(marketplace.reviews_for(m.id)),
            install_count=marketplace.install_count(m.id),
        )
        for m in listings
    ]


@router.get("/marketplace/categories", response_model=list[str])
def list_categories(
    marketplace: MarketplaceEngine = Depends(get_marketplace_engine),
) -> list[str]:
    return [c.value for c in marketplace.categories()]


@router.get("/plugins/{plugin_id}", response_model=PluginManifestResponse)
def get_plugin(
    plugin_id: str, registry: InMemoryPluginRegistry = Depends(get_plugin_registry)
) -> PluginManifestResponse:
    return _to_manifest_response(_get_manifest_or_404(plugin_id, registry))


@router.post("/plugins/{plugin_id}/validate", response_model=PluginManifestResponse)
def validate_plugin(
    plugin_id: str,
    request: PublishingActionRequest,
    publishing: PublishingEngine = Depends(get_publishing_engine),
) -> PluginManifestResponse:
    try:
        manifest = publishing.validate_manifest(plugin_id, actor=request.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"plugin {plugin_id} not found") from exc
    except ValidationFailedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidPublishingTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest_response(manifest)


@router.post("/plugins/{plugin_id}/sign", response_model=PluginManifestResponse)
def sign_plugin(
    plugin_id: str,
    request: PublishingActionRequest,
    publishing: PublishingEngine = Depends(get_publishing_engine),
) -> PluginManifestResponse:
    try:
        manifest = publishing.sign_manifest(plugin_id, actor=request.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"plugin {plugin_id} not found") from exc
    except InvalidPublishingTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest_response(manifest)


@router.post("/plugins/{plugin_id}/publish", response_model=PluginManifestResponse)
def publish_plugin(
    plugin_id: str,
    request: PublishingActionRequest,
    publishing: PublishingEngine = Depends(get_publishing_engine),
) -> PluginManifestResponse:
    try:
        manifest = publishing.publish(plugin_id, actor=request.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"plugin {plugin_id} not found") from exc
    except InvalidPublishingTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest_response(manifest)


@router.post("/plugins/{plugin_id}/retire", response_model=PluginManifestResponse)
def retire_plugin(
    plugin_id: str,
    request: PublishingActionRequest,
    publishing: PublishingEngine = Depends(get_publishing_engine),
) -> PluginManifestResponse:
    try:
        manifest = publishing.retire(plugin_id, actor=request.actor, reason=request.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"plugin {plugin_id} not found") from exc
    except InvalidPublishingTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_manifest_response(manifest)


@router.get("/plugins/{plugin_id}/publishing-history", response_model=list[PublishingEventResponse])
def get_publishing_history(
    plugin_id: str, publishing: PublishingEngine = Depends(get_publishing_engine)
) -> list[PublishingEventResponse]:
    return [
        PublishingEventResponse(
            id=e.id,
            from_status=e.from_status.value,
            to_status=e.to_status.value,
            actor=e.actor,
            reason=e.reason,
            created_at=e.created_at,
        )
        for e in publishing.history(plugin_id)
    ]


@router.post("/marketplace/{plugin_id}/install", response_model=ExtensionInstanceResponse)
def install_plugin(
    plugin_id: str,
    request: InstallRequest,
    extensions: ExtensionEngine = Depends(get_extension_engine),
) -> ExtensionInstanceResponse:
    requested = frozenset(ExtensionPermission(p) for p in request.permissions)
    try:
        instance = extensions.install(request.firm_id, plugin_id, requested)
    except PluginNotAvailableError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UngrantablePermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_extension_response(instance)


@router.post("/marketplace/{plugin_id}/uninstall", response_model=ExtensionInstanceResponse)
def uninstall_plugin(
    plugin_id: str, firm_id: str, extensions: ExtensionEngine = Depends(get_extension_engine)
) -> ExtensionInstanceResponse:
    try:
        instance = extensions.uninstall(firm_id, plugin_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="extension not installed") from exc
    return _to_extension_response(instance)


@router.post("/marketplace/{plugin_id}/update", response_model=ExtensionInstanceResponse)
def update_plugin(
    plugin_id: str, firm_id: str, extensions: ExtensionEngine = Depends(get_extension_engine)
) -> ExtensionInstanceResponse:
    try:
        instance = extensions.update(firm_id, plugin_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="extension not installed") from exc
    return _to_extension_response(instance)


@router.get("/extensions", response_model=list[ExtensionInstanceResponse])
def list_extensions(
    firm_id: str, extensions: ExtensionEngine = Depends(get_extension_engine)
) -> list[ExtensionInstanceResponse]:
    return [_to_extension_response(i) for i in extensions.list_for_firm(firm_id)]


@router.post("/marketplace/{plugin_id}/reviews", response_model=ReviewResponse)
def submit_review(
    plugin_id: str,
    request: ReviewRequest,
    marketplace: MarketplaceEngine = Depends(get_marketplace_engine),
) -> ReviewResponse:
    try:
        review = marketplace.submit_review(
            plugin_id, request.firm_id, request.rating, request.comment
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewResponse(
        id=review.id,
        plugin_id=review.plugin_id,
        firm_id=review.firm_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.get("/marketplace/{plugin_id}/reviews", response_model=list[ReviewResponse])
def list_reviews(
    plugin_id: str, marketplace: MarketplaceEngine = Depends(get_marketplace_engine)
) -> list[ReviewResponse]:
    return [
        ReviewResponse(
            id=r.id,
            plugin_id=r.plugin_id,
            firm_id=r.firm_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in marketplace.reviews_for(plugin_id)
    ]


@router.get("/developer-portal", response_model=list[PortalResourceResponse])
def list_developer_portal_resources(
    type: str | None = None,  # noqa: A002 — mirrors the query-param name
    keyword: str | None = None,
    portal: DeveloperPortalService = Depends(get_developer_portal_service),
) -> list[PortalResourceResponse]:
    if keyword:
        resources = portal.search(keyword)
    elif type:
        resources = portal.list_by_type(ResourceType(type))
    else:
        resources = portal.list_all()
    return [
        PortalResourceResponse(
            id=r.id, title=r.title, type=r.type.value, path=r.path, summary=r.summary
        )
        for r in resources
    ]
