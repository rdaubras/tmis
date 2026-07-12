from pydantic import BaseModel


class ConnectorResponse(BaseModel):
    id: str
    name: str
    version: str
    publisher: str
    connector_type: str
    capabilities: list[str]
    status: str


class ConnectorConfigurationRequest(BaseModel):
    firm_id: str
    values: dict[str, str]
    actor_id: str | None = None


class ConnectorConfigurationResponse(BaseModel):
    connector_id: str
    firm_id: str
    values: dict[str, str]
    enabled: bool


class SyncJobCreateRequest(BaseModel):
    firm_id: str
    connector_id: str
    entity_type: str
    direction: str = "pull"
    mode: str = "incremental"
    conflict_strategy: str = "remote_wins"


class SyncJobResponse(BaseModel):
    id: str
    connector_id: str
    firm_id: str
    entity_type: str
    direction: str
    mode: str
    conflict_strategy: str
    enabled: bool


class SyncRunResponse(BaseModel):
    job_id: str
    records_read: int
    records_written: int
    conflicts: int
    conflicts_pending_validation: int


class WebhookSubscriptionRequest(BaseModel):
    firm_id: str
    connector_id: str
    url: str
    direction: str
    secret: str
    event_types: list[str] = []


class WebhookSubscriptionResponse(BaseModel):
    id: str
    connector_id: str
    firm_id: str
    url: str
    direction: str
    event_types: list[str]
    enabled: bool


class WebhookInboundRequest(BaseModel):
    firm_id: str
    entity_type: str
    external_id: str
    payload: dict[str, str]
    signature: str


class ComponentHealthResponse(BaseModel):
    name: str
    status: str
    detail: str
    latency_ms: float


class SystemHealthResponse(BaseModel):
    status: str
    components: list[ComponentHealthResponse]
