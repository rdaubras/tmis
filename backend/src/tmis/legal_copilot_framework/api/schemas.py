from pydantic import BaseModel


class CopilotRegisterRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    description: str
    version: str
    author: str = "unknown"
    compatibility: str = "*"
    license: str = "proprietary"
    dependencies: tuple[str, ...] = ()
    agent_ids: tuple[str, ...] = ()
    compatible_models: frozenset[str] = frozenset()
    workflow_pack_ids: tuple[str, ...] = ()
    document_pack_ids: tuple[str, ...] = ()
    knowledge_pack_ids: tuple[str, ...] = ()
    reasoning_pack_ids: tuple[str, ...] = ()
    prompt_pack_id: str | None = None
    validation_policy_ids: tuple[str, ...] = ()
    permissions: frozenset[str] = frozenset()
    metrics_enabled: bool = True


class LegalCopilotResponse(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    version: str
    team_id: str
    status: str
    dependencies: tuple[str, ...]
    compatible_models: frozenset[str]
    prompt_pack_id: str | None
    knowledge_pack_ids: tuple[str, ...]
    reasoning_pack_ids: tuple[str, ...]
    document_pack_ids: tuple[str, ...]
    workflow_pack_ids: tuple[str, ...]
    validation_policy_ids: tuple[str, ...]
    permissions: frozenset[str]
    metrics_enabled: bool
    created_at: str


class CopilotActivationRequest(BaseModel):
    firm_id: str
    user_id: str


class CopilotActivationResponse(BaseModel):
    firm_id: str
    copilot_id: str
    active: bool
    version: str
    granted_permissions: frozenset[str]
    updated_at: str


class CopilotManifestResponse(BaseModel):
    copilot_id: str
    version: str
    domain: str
    author: str
    status: str
    dependencies: tuple[str, ...]
    compatibility: str
    license: str
    published_at: str


class PromptPackPublishRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    system_prompt_ids: tuple[str, ...] = ()
    business_prompt_ids: tuple[str, ...] = ()
    parent_pack_id: str | None = None
    overrides: dict[str, str] = {}


class KnowledgePackPublishRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    taxonomy_root_id: str | None = None
    source_refs: tuple[str, ...] = ()
    update_rules: tuple[str, ...] = ()
    quality_controls: tuple[str, ...] = ()
    knowledge_object_ids: tuple[str, ...] = ()


class ReasoningPackPublishRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    strategy_types: frozenset[str]
    pattern_ids: tuple[str, ...] = ()


class DocumentPackPublishRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    document_types: tuple[str, ...] = ()
    cabinet_template_ids: tuple[str, ...] = ()
    validations: tuple[str, ...] = ()
    quality_controls: tuple[str, ...] = ()


class WorkflowPackPublishRequest(BaseModel):
    firm_id: str
    user_id: str
    id: str
    name: str
    domain: str
    workflow_template_ids: tuple[str, ...] = ()


class PackPublishResponse(BaseModel):
    id: str
    name: str
    domain: str
    version: int


class CopilotMetricsResponse(BaseModel):
    copilot_id: str
    usage_count: int
    total_ai_cost_usd: float
    avg_response_time_ms: float
    validation_rate: float
    pack_reuse_count: int
    satisfaction_score: float | None


class DemoSeedRequest(BaseModel):
    firm_id: str
    user_id: str


class DemoSeedResponse(BaseModel):
    copilot_ids: list[str]


class MarketplacePublishRequest(BaseModel):
    firm_id: str
    user_id: str


class MarketplacePublishResponse(BaseModel):
    plugin_id: str
    plugin_type: str
    version: str
    status: str
    signature: str | None
