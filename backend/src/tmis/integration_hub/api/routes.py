import json
import uuid

from fastapi import APIRouter, Depends, HTTPException

from tmis.integration_hub.api.schemas import (
    ComponentHealthResponse,
    ConnectorConfigurationRequest,
    ConnectorConfigurationResponse,
    ConnectorResponse,
    SyncJobCreateRequest,
    SyncJobResponse,
    SyncRunResponse,
    SystemHealthResponse,
    WebhookInboundRequest,
    WebhookSubscriptionRequest,
    WebhookSubscriptionResponse,
)
from tmis.integration_hub.bootstrap import (
    get_configuration_engine,
    get_connector_registry_engine,
    get_health_check_engine,
    get_mapping_engine,
    get_sync_job_store,
    get_synchronization_engine,
    get_webhook_engine,
    get_webhook_subscription_store,
)
from tmis.integration_hub.configuration.engine import (
    ConfigurationEngine,
    ConfigurationValidationError,
)
from tmis.integration_hub.connector_registry.engine import ConnectorRegistryEngine
from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor
from tmis.integration_hub.event_bridge.schemas import EventDirection
from tmis.integration_hub.mapping.engine import ConnectorMapper, MappingEngine
from tmis.integration_hub.synchronization.engine import SynchronizationEngine
from tmis.integration_hub.synchronization.schemas import (
    SyncDirection,
    SyncJobConfig,
    SyncMode,
    SyncRunReport,
)
from tmis.integration_hub.synchronization.store import InMemorySyncJobStore
from tmis.integration_hub.webhooks.engine import WebhookEngine
from tmis.integration_hub.webhooks.schemas import WebhookSubscription
from tmis.integration_hub.webhooks.store import InMemoryWebhookSubscriptionStore

router = APIRouter(prefix="/integration-hub", tags=["integration-hub"])


def _connector_response(descriptor: ConnectorDescriptor) -> ConnectorResponse:
    return ConnectorResponse(
        id=descriptor.id,
        name=descriptor.name,
        version=descriptor.version,
        publisher=descriptor.publisher,
        connector_type=descriptor.connector_type.value,
        capabilities=[c.value for c in descriptor.capabilities],
        status=descriptor.status.value,
    )


@router.get("/connectors", response_model=list[ConnectorResponse])
def list_connectors(
    registry: ConnectorRegistryEngine = Depends(get_connector_registry_engine),
) -> list[ConnectorResponse]:
    return [_connector_response(d) for d in registry.list_connectors()]


@router.post("/connectors/{connector_id}/disable", response_model=ConnectorResponse)
def disable_connector(
    connector_id: str,
    registry: ConnectorRegistryEngine = Depends(get_connector_registry_engine),
) -> ConnectorResponse:
    try:
        registry.disable(connector_id)
        descriptor = registry.get_descriptor(connector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _connector_response(descriptor)


@router.post("/connectors/{connector_id}/enable", response_model=ConnectorResponse)
def enable_connector(
    connector_id: str,
    registry: ConnectorRegistryEngine = Depends(get_connector_registry_engine),
) -> ConnectorResponse:
    try:
        registry.enable(connector_id)
        descriptor = registry.get_descriptor(connector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _connector_response(descriptor)


@router.put(
    "/connectors/{connector_id}/configuration", response_model=ConnectorConfigurationResponse
)
def set_connector_configuration(
    connector_id: str,
    payload: ConnectorConfigurationRequest,
    registry: ConnectorRegistryEngine = Depends(get_connector_registry_engine),
    config_engine: ConfigurationEngine = Depends(get_configuration_engine),
) -> ConnectorConfigurationResponse:
    try:
        descriptor = registry.get_descriptor(connector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        configuration = config_engine.set_configuration(
            connector_id, payload.firm_id, payload.values, descriptor
        )
    except ConfigurationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ConnectorConfigurationResponse(
        connector_id=configuration.connector_id,
        firm_id=configuration.firm_id,
        values=configuration.values,
        enabled=configuration.enabled,
    )


@router.get(
    "/connectors/{connector_id}/configuration", response_model=ConnectorConfigurationResponse
)
def get_connector_configuration(
    connector_id: str,
    firm_id: str,
    config_engine: ConfigurationEngine = Depends(get_configuration_engine),
) -> ConnectorConfigurationResponse:
    configuration = config_engine.get_configuration(firm_id, connector_id)
    if configuration is None:
        raise HTTPException(status_code=404, detail="configuration not found")
    return ConnectorConfigurationResponse(
        connector_id=configuration.connector_id,
        firm_id=configuration.firm_id,
        values=configuration.values,
        enabled=configuration.enabled,
    )


def _sync_job_response(job: SyncJobConfig) -> SyncJobResponse:
    return SyncJobResponse(
        id=job.id,
        connector_id=job.connector_id,
        firm_id=job.firm_id,
        entity_type=job.entity_type,
        direction=job.direction.value,
        mode=job.mode.value,
        conflict_strategy=job.conflict_strategy.value,
        enabled=job.enabled,
    )


@router.post("/sync-jobs", response_model=SyncJobResponse)
def create_sync_job(
    payload: SyncJobCreateRequest,
    store: InMemorySyncJobStore = Depends(get_sync_job_store),
) -> SyncJobResponse:
    try:
        job = SyncJobConfig(
            id=f"sync-{uuid.uuid4().hex[:12]}",
            connector_id=payload.connector_id,
            firm_id=payload.firm_id,
            entity_type=payload.entity_type,
            direction=SyncDirection(payload.direction),
            mode=SyncMode(payload.mode),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store.save(job)
    return _sync_job_response(job)


@router.get("/sync-jobs", response_model=list[SyncJobResponse])
def list_sync_jobs(
    firm_id: str,
    store: InMemorySyncJobStore = Depends(get_sync_job_store),
) -> list[SyncJobResponse]:
    return [_sync_job_response(j) for j in store.list_all(firm_id)]


@router.post("/sync-jobs/{job_id}/run", response_model=SyncRunResponse)
async def run_sync_job(
    job_id: str,
    firm_id: str,
    store: InMemorySyncJobStore = Depends(get_sync_job_store),
    registry: ConnectorRegistryEngine = Depends(get_connector_registry_engine),
    config_engine: ConfigurationEngine = Depends(get_configuration_engine),
    mapping_engine: MappingEngine = Depends(get_mapping_engine),
    sync_engine: SynchronizationEngine = Depends(get_synchronization_engine),
) -> SyncRunResponse:
    job = store.get(firm_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="sync job not found")
    try:
        implementation = registry.get_implementation(job.connector_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    configuration = config_engine.get_configuration(firm_id, job.connector_id)
    config_values = configuration.values if configuration is not None else {}
    mapper = ConnectorMapper(mapping_engine, connector_id=job.connector_id, firm_id=firm_id)

    report: SyncRunReport = await sync_engine.run_pull(
        job, implementation, config_values, mapper=mapper
    )
    return SyncRunResponse(
        job_id=report.job_id,
        records_read=report.result.records_read,
        records_written=report.result.records_written,
        conflicts=report.result.conflicts,
        conflicts_pending_validation=report.conflicts_pending_validation,
    )


@router.post("/webhooks", response_model=WebhookSubscriptionResponse)
def create_webhook_subscription(
    payload: WebhookSubscriptionRequest,
    store: InMemoryWebhookSubscriptionStore = Depends(get_webhook_subscription_store),
) -> WebhookSubscriptionResponse:
    try:
        direction = EventDirection(payload.direction)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    subscription = WebhookSubscription(
        id=f"webhook-{uuid.uuid4().hex[:12]}",
        connector_id=payload.connector_id,
        firm_id=payload.firm_id,
        url=payload.url,
        direction=direction,
        secret=payload.secret,
        event_types=tuple(payload.event_types),
    )
    store.save(subscription)
    return WebhookSubscriptionResponse(
        id=subscription.id,
        connector_id=subscription.connector_id,
        firm_id=subscription.firm_id,
        url=subscription.url,
        direction=subscription.direction.value,
        event_types=list(subscription.event_types),
        enabled=subscription.enabled,
    )


@router.post("/webhooks/{subscription_id}/inbound", response_model=bool)
async def receive_inbound_webhook(
    subscription_id: str,
    payload: WebhookInboundRequest,
    store: InMemoryWebhookSubscriptionStore = Depends(get_webhook_subscription_store),
    webhook_engine: WebhookEngine = Depends(get_webhook_engine),
) -> bool:
    subscription = store.get(payload.firm_id, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="webhook subscription not found")

    raw_body = json.dumps(
        {
            "entity_type": payload.entity_type,
            "external_id": payload.external_id,
            "payload": payload.payload,
        },
        sort_keys=True,
    ).encode()
    return await webhook_engine.receive_inbound(
        subscription,
        raw_body,
        payload.signature,
        payload.entity_type,
        payload.external_id,
        payload.payload,
    )


@router.get("/health", response_model=SystemHealthResponse)
def get_health() -> SystemHealthResponse:
    engine = get_health_check_engine()
    result = engine.readiness()
    return SystemHealthResponse(
        status=result.status.value,
        components=[
            ComponentHealthResponse(
                name=c.name, status=c.status.value, detail=c.detail, latency_ms=c.latency_ms
            )
            for c in result.components
        ],
    )
