import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.licenses.store import (
    InMemoryFloatingPoolStore,
    InMemoryLicenseGrantStore,
)
from tmis.business_platform.marketplace_subscriptions.engine import MarketplaceSubscriptionEngine
from tmis.business_platform.marketplace_subscriptions.store import (
    InMemoryExtensionSubscriptionStore,
)
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)
from tmis.legal_copilot_framework.copilot.engine import CopilotEngine
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus, LegalCopilot
from tmis.legal_copilot_framework.copilot.store import InMemoryCopilotStore
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest
from tmis.legal_copilot_framework.registry.store import InMemoryCopilotRegistryStore
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

FIRM = "firm-a"
ACTOR = "partner-a"


def _copilot(copilot_id: str = "copilot-1") -> LegalCopilot:
    return LegalCopilot(
        id=copilot_id,
        name="Copilote",
        domain=LegalDomain.CIVIL,
        description="desc",
        version="1.0.0",
        dependencies=(),
        team_id="team-1",
        compatible_models=frozenset(),
        prompt_pack_id=None,
        knowledge_pack_ids=(),
        reasoning_pack_ids=(),
        document_pack_ids=(),
        workflow_pack_ids=(),
        validation_policy_ids=(),
        permissions=frozenset(),
    )


def _manifest(copilot_id: str = "copilot-1") -> CopilotManifest:
    return CopilotManifest(
        copilot_id=copilot_id,
        version="1.0.0",
        domain=LegalDomain.CIVIL,
        author="author-1",
        status=CopilotStatus.DRAFT,
    )


def _engine() -> tuple[CopilotEngine, CopilotRegistry]:
    plugin_registry = InMemoryPluginRegistry()
    permissions = PermissionEngine(InMemoryPermissionStore())
    extensions = ExtensionEngine(InMemoryExtensionStore(), plugin_registry, permissions)
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
    engine = CopilotEngine(
        InMemoryCopilotStore(), registry, plugin_registry, publishing, extensions, subscriptions
    )
    return engine, registry


def _define_and_register(
    engine: CopilotEngine, registry: CopilotRegistry, copilot_id: str = "copilot-1"
) -> None:
    engine.define(_copilot(copilot_id))
    registry.register(_manifest(copilot_id))


def test_define_and_get_roundtrip() -> None:
    engine, _ = _engine()
    copilot = _copilot()
    engine.define(copilot)

    assert engine.get("copilot-1") == copilot


def test_get_unknown_copilot_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_list_all_returns_every_defined_copilot() -> None:
    engine, _ = _engine()
    engine.define(_copilot("copilot-1"))
    engine.define(_copilot("copilot-2"))

    assert {c.id for c in engine.list_all()} == {"copilot-1", "copilot-2"}


def test_activate_requires_the_copilot_to_exist() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.activate(FIRM, "missing", ACTOR)


def test_activate_then_deactivate_toggles_is_active() -> None:
    engine, registry = _engine()
    _define_and_register(engine, registry)

    assert engine.is_active(FIRM, "copilot-1") is False

    engine.activate(FIRM, "copilot-1", ACTOR)
    assert engine.is_active(FIRM, "copilot-1") is True

    engine.deactivate(FIRM, "copilot-1")
    assert engine.is_active(FIRM, "copilot-1") is False


def test_activate_publishes_the_copilot_and_returns_its_version_and_permissions() -> None:
    engine, registry = _engine()
    _define_and_register(engine, registry)

    activation = engine.activate(FIRM, "copilot-1", ACTOR)

    assert activation.version == "1.0.0"
    assert activation.granted_permissions == frozenset()


def test_active_copilots_only_lists_activated_ones_for_that_firm() -> None:
    engine, registry = _engine()
    _define_and_register(engine, registry, "copilot-1")
    _define_and_register(engine, registry, "copilot-2")
    engine.activate(FIRM, "copilot-1", ACTOR)

    assert [c.id for c in engine.active_copilots(FIRM)] == ["copilot-1"]
    assert engine.active_copilots("other-firm") == []
