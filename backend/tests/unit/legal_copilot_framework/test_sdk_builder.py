import pytest

from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.prompt_optimizer.engine import PromptOptimizer
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.registry.store import InMemoryAgentRegistry
from tmis.ai_team.teams.engine import TeamBuilder
from tmis.ai_team.teams.store import InMemoryTeamStore
from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.licenses.store import (
    InMemoryFloatingPoolStore,
    InMemoryLicenseGrantStore,
)
from tmis.business_platform.marketplace_subscriptions.engine import MarketplaceSubscriptionEngine
from tmis.business_platform.marketplace_subscriptions.store import (
    InMemoryExtensionSubscriptionStore,
)
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.templates.engine import CabinetTemplateEngine
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus
from tmis.legal_copilot_framework.copilot.store import InMemoryCopilotStore
from tmis.legal_copilot_framework.document_packs.engine import DocumentPackEngine
from tmis.legal_copilot_framework.document_packs.store import InMemoryDocumentPackStore
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.store import InMemoryKnowledgePackStore
from tmis.legal_copilot_framework.prompt_packs.engine import PromptPackEngine
from tmis.legal_copilot_framework.prompt_packs.store import InMemoryPromptPackStore
from tmis.legal_copilot_framework.reasoning_packs.engine import ReasoningPackEngine
from tmis.legal_copilot_framework.reasoning_packs.store import InMemoryReasoningPackStore
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.registry.store import InMemoryCopilotRegistryStore
from tmis.legal_copilot_framework.sdk.builder import CopilotBuilder, CopilotValidationError
from tmis.legal_copilot_framework.sdk.schemas import CopilotSpec
from tmis.legal_copilot_framework.validation_policies.engine import ValidationPolicyEngine
from tmis.legal_copilot_framework.validation_policies.store import (
    InMemoryCopilotValidationPolicyStore,
)
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine
from tmis.legal_copilot_framework.workflow_packs.store import InMemoryWorkflowPackStore
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.store import InMemoryExtensionStore
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.marketplace.store import InMemoryReviewStore
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.publishing.engine import PublishingEngine
from tmis.platform_sdk.publishing.store import InMemoryPublishingStore
from tmis.platform_sdk.validation.engine import PluginValidator
from tmis.workflow_automation.template_library.defaults import build_default_templates
from tmis.workflow_automation.template_library.engine import TemplateLibrary
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine
from tmis.workflow_automation.workflow_engine.store import InMemoryWorkflowStore

_BuilderFixture = tuple[
    CopilotBuilder, PromptPackEngine, KnowledgePackEngine, CopilotEngine, CopilotRegistry
]


def _builder() -> _BuilderFixture:
    prompt_registry = PromptRegistry()
    prompt_packs = PromptPackEngine(
        InMemoryPromptPackStore(), prompt_registry, PromptOptimizer(prompt_registry)
    )
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    knowledge_packs = KnowledgePackEngine(InMemoryKnowledgePackStore(), space)
    reasoning_packs = ReasoningPackEngine(InMemoryReasoningPackStore(), space)
    document_packs = DocumentPackEngine(
        InMemoryDocumentPackStore(), TemplateRegistry(), CabinetTemplateEngine(space)
    )
    library = TemplateLibrary(WorkflowEngine(InMemoryWorkflowStore()))
    for template in build_default_templates():
        library.register(template)
    workflow_packs = WorkflowPackEngine(InMemoryWorkflowPackStore(), library)
    validation_policies = ValidationPolicyEngine(
        InMemoryCopilotValidationPolicyStore(),
        PolicyEngine(InMemoryGovernancePolicyStore()),
        HumanValidationEngine(InMemoryValidationStore()),
    )
    team_builder = TeamBuilder(InMemoryAgentRegistry(), InMemoryTeamStore())

    plugin_registry = InMemoryPluginRegistry()
    permission_engine = PermissionEngine(InMemoryPermissionStore())
    extensions = ExtensionEngine(InMemoryExtensionStore(), plugin_registry, permission_engine)
    marketplace = MarketplaceEngine(plugin_registry, InMemoryReviewStore(), extensions)
    signer = LicenseKeySigner(secret="test-secret-0123456789abcdef")
    licenses = LicenseEngine(InMemoryLicenseGrantStore(), InMemoryFloatingPoolStore(), signer)
    billing = BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        ManualPaymentGateway(),
        NoOpAccountingExport(),
    )
    subscriptions = MarketplaceSubscriptionEngine(
        marketplace, licenses, billing, InMemoryExtensionSubscriptionStore()
    )
    publishing = PublishingEngine(
        InMemoryPublishingStore(), plugin_registry, PluginValidator(plugin_registry, signer)
    )
    registry = CopilotRegistry(InMemoryCopilotRegistryStore())
    copilot_engine = CopilotEngine(
        InMemoryCopilotStore(), registry, plugin_registry, publishing, extensions, subscriptions
    )
    builder = CopilotBuilder(
        team_builder,
        copilot_engine,
        registry,
        prompt_packs,
        knowledge_packs,
        reasoning_packs,
        document_packs,
        workflow_packs,
        validation_policies,
    )
    return builder, prompt_packs, knowledge_packs, copilot_engine, registry


def _spec(**overrides: object) -> CopilotSpec:
    defaults: dict[str, object] = dict(
        id="copilot-1",
        name="Copilote",
        domain=LegalDomain.CIVIL,
        description="desc",
        version="1.0.0",
    )
    defaults.update(overrides)
    return CopilotSpec(**defaults)  # type: ignore[arg-type]


def test_build_with_no_pack_references_succeeds() -> None:
    builder, _, _, _, _ = _builder()

    copilot = builder.build(_spec())

    assert copilot.id == "copilot-1"
    assert copilot.team_id


def test_build_registers_the_copilot_and_a_draft_manifest() -> None:
    builder, _, _, copilot_engine, registry = _builder()

    builder.build(_spec())

    manifest = registry.get_latest("copilot-1")
    assert manifest.status is CopilotStatus.DRAFT
    assert copilot_engine.get("copilot-1").id == "copilot-1"


def test_build_rejects_a_missing_prompt_pack_reference() -> None:
    builder, _, _, _, _ = _builder()

    with pytest.raises(CopilotValidationError, match="prompt pack not found"):
        builder.build(_spec(prompt_pack_id="missing-pack"))


def test_build_rejects_a_missing_knowledge_pack_reference() -> None:
    builder, _, _, _, _ = _builder()

    with pytest.raises(CopilotValidationError, match="knowledge pack not found"):
        builder.build(_spec(knowledge_pack_ids=("missing-pack",)))


def test_build_accepts_a_resolvable_prompt_pack_reference() -> None:
    builder, prompt_packs, _, _, _ = _builder()
    pack = prompt_packs.register_pack("pp-1", "Pack", LegalDomain.CIVIL)

    copilot = builder.build(_spec(prompt_pack_id=pack.id))

    assert copilot.prompt_pack_id == pack.id


def test_build_collects_every_validation_error_at_once() -> None:
    builder, _, _, _, _ = _builder()

    with pytest.raises(CopilotValidationError) as excinfo:
        builder.build(
            _spec(
                prompt_pack_id="missing-prompt",
                knowledge_pack_ids=("missing-knowledge",),
            )
        )

    assert "prompt pack not found" in str(excinfo.value)
    assert "knowledge pack not found" in str(excinfo.value)
