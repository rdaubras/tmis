from functools import lru_cache

from tmis.ai_fabric.bootstrap import get_prompt_optimizer, get_prompt_registry
from tmis.ai_governance.bootstrap import get_human_validation_engine, get_policy_engine
from tmis.ai_team.bootstrap import get_team_builder
from tmis.business_platform.bootstrap import get_marketplace_subscription_engine
from tmis.cabinet_knowledge.bootstrap import get_knowledge_space, get_writing_style_engine
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.cloud_operations.bootstrap import get_metrics_engine
from tmis.identity_platform.bootstrap import get_tenant_context_engine
from tmis.legal_copilot_framework.context_engine.engine import ContextEngine
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.marketplace import to_plugin_manifest
from tmis.legal_copilot_framework.copilot.store import InMemoryCopilotStore
from tmis.legal_copilot_framework.copilots.deps import DemoCopilotDeps
from tmis.legal_copilot_framework.copilots.seed import seed_demo_copilots
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.document_packs.store import InMemoryDocumentPackStore
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.store import InMemoryKnowledgePackStore
from tmis.legal_copilot_framework.metrics.engine import CopilotMetricsEngine
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.prompt_packs.store import InMemoryPromptPackStore
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.reasoning_packs.store import InMemoryReasoningPackStore
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.registry.store import InMemoryCopilotRegistryStore
from tmis.legal_copilot_framework.sdk.builder import CopilotBuilder
from tmis.legal_copilot_framework.validation_policies.engine import ValidationPolicyEngine
from tmis.legal_copilot_framework.validation_policies.store import (
    InMemoryCopilotValidationPolicyStore,
)
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine
from tmis.legal_copilot_framework.workflow_packs.store import InMemoryWorkflowPackStore
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.platform_sdk.bootstrap import (
    get_extension_engine,
    get_plugin_registry,
    get_publishing_engine,
)
from tmis.platform_sdk.plugin_system.schemas import PluginManifest
from tmis.workflow_automation.bootstrap import get_template_library

_DEMO_FIRM_ID = "demo-firm"
"""The fictional firm the sprint's five MVP copilots register their
prompts/knowledge against — Phase 12 explicitly asks for fictional
data, never a real tenant's."""


@lru_cache
def get_prompt_pack_engine() -> PromptPackEngine:
    return PromptPackEngine(
        InMemoryPromptPackStore(), get_prompt_registry(), get_prompt_optimizer()
    )


@lru_cache
def get_knowledge_pack_engine() -> KnowledgePackEngine:
    return KnowledgePackEngine(InMemoryKnowledgePackStore(), get_knowledge_space())


@lru_cache
def get_reasoning_pack_engine() -> ReasoningPackEngine:
    return ReasoningPackEngine(InMemoryReasoningPackStore(), get_knowledge_space())


@lru_cache
def get_document_pack_engine() -> DocumentPackEngine:
    return DocumentPackEngine(
        InMemoryDocumentPackStore(), get_template_registry(), get_cabinet_template_engine()
    )


@lru_cache
def get_workflow_pack_engine() -> WorkflowPackEngine:
    return WorkflowPackEngine(InMemoryWorkflowPackStore(), get_template_library())


@lru_cache
def get_validation_policy_engine() -> ValidationPolicyEngine:
    return ValidationPolicyEngine(
        InMemoryCopilotValidationPolicyStore(), get_policy_engine(), get_human_validation_engine()
    )


@lru_cache
def get_context_engine() -> ContextEngine:
    return ContextEngine(
        get_tenant_context_engine(),
        get_knowledge_space(),
        get_writing_style_engine(),
        get_policy_engine(),
    )


@lru_cache
def get_copilot_metrics_engine() -> CopilotMetricsEngine:
    return CopilotMetricsEngine(get_metrics_engine())


@lru_cache
def get_copilot_registry() -> CopilotRegistry:
    return CopilotRegistry(InMemoryCopilotRegistryStore())


@lru_cache
def get_copilot_engine() -> CopilotEngine:
    return CopilotEngine(
        InMemoryCopilotStore(),
        get_copilot_registry(),
        get_plugin_registry(),
        get_publishing_engine(),
        get_extension_engine(),
        get_marketplace_subscription_engine(),
    )


@lru_cache
def get_copilot_builder() -> CopilotBuilder:
    return CopilotBuilder(
        get_team_builder(),
        get_copilot_engine(),
        get_copilot_registry(),
        get_prompt_pack_engine(),
        get_knowledge_pack_engine(),
        get_reasoning_pack_engine(),
        get_document_pack_engine(),
        get_workflow_pack_engine(),
        get_validation_policy_engine(),
    )


@lru_cache
def get_template_registry() -> TemplateRegistry:
    return TemplateRegistry()


@lru_cache
def get_cabinet_template_engine() -> CabinetTemplateEngine:
    return CabinetTemplateEngine(get_knowledge_space())


@lru_cache
def seed_demo_copilots_once() -> list[str]:
    """Builds the sprint's five MVP copilots exactly once per process
    (Phase 12) and returns their ids — `@lru_cache` makes re-entry a
    no-op, so the API layer can call this lazily on first use instead
    of every deployment needing an explicit seed script."""
    deps = DemoCopilotDeps(
        firm_id=_DEMO_FIRM_ID,
        prompt_registry=get_prompt_registry(),
        prompt_packs=get_prompt_pack_engine(),
        knowledge_space=get_knowledge_space(),
        knowledge_packs=get_knowledge_pack_engine(),
        reasoning_packs=get_reasoning_pack_engine(),
        document_packs=get_document_pack_engine(),
        workflow_packs=get_workflow_pack_engine(),
        template_library=get_template_library(),
        validation_policies=get_validation_policy_engine(),
        builder=get_copilot_builder(),
    )
    return [copilot.id for copilot in seed_demo_copilots(deps)]


def publish_copilot_to_marketplace(copilot_id: str, actor: str) -> PluginManifest:
    """Runs a registered copilot through the existing `platform_sdk`
    publishing pipeline (Développement → Validation → Signature →
    Publication) unchanged, so it lands in `platform_sdk.marketplace`
    exactly like any other plugin — see `copilot.marketplace.
    to_plugin_manifest` for the one-way conversion this wraps."""
    copilot = get_copilot_engine().get(copilot_id)
    manifest = get_copilot_registry().get_latest(copilot_id)
    plugin_manifest = to_plugin_manifest(copilot, manifest)
    get_plugin_registry().register(plugin_manifest)
    publishing = get_publishing_engine()
    publishing.validate_manifest(copilot_id, actor)
    publishing.sign_manifest(copilot_id, actor)
    return publishing.publish(copilot_id, actor)
