from tmis.ai_fabric.quotas.engine import QuotaEngine as AIQuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore as AIInMemoryQuotaStore
from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.business_platform.customer_portal.engine import CustomerPortalEngine
from tmis.business_platform.licenses.engine import LicenseEngine
from tmis.business_platform.licenses.store import (
    InMemoryFloatingPoolStore,
    InMemoryLicenseGrantStore,
)
from tmis.business_platform.marketplace_subscriptions.engine import MarketplaceSubscriptionEngine
from tmis.business_platform.marketplace_subscriptions.store import (
    InMemoryExtensionSubscriptionStore,
)
from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.store import InMemoryMeteringEventStore
from tmis.business_platform.modules.engine import ModuleRegistry
from tmis.business_platform.modules.store import InMemoryModuleActivationStore
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.store import InMemoryQuotaOverrideStore
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.tenant_settings.engine import TenantSettingsEngine
from tmis.business_platform.tenant_settings.store import InMemoryTenantSettingsStore
from tmis.business_platform.usage.engine import UsageEngine
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)
from tmis.identity_platform.roles.engine import RoleEngine
from tmis.identity_platform.roles.schemas import Role
from tmis.identity_platform.roles.store import InMemoryRoleAssignmentStore
from tmis.identity_platform.users.engine import UserEngine
from tmis.identity_platform.users.store import InMemoryUserStore
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.store import InMemoryExtensionStore
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.marketplace.store import InMemoryReviewStore
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import (
    PluginManifest,
    PluginType,
    PublishingStatus,
)


def _customer_portal(firm_id: str = "firm-1") -> CustomerPortalEngine:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(PlanName.PROFESSIONAL)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id)

    licenses = LicenseEngine(
        InMemoryLicenseGrantStore(),
        InMemoryFloatingPoolStore(),
        LicenseKeySigner(secret="test-secret-0123456789abcdef"),
    )
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    ai_quotas = AIQuotaEngine(AIInMemoryQuotaStore())
    quotas = BusinessQuotaEngine(catalog, subs, InMemoryQuotaOverrideStore(), ai_quotas)
    cost_tracker = CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore())
    token_manager = TokenManager(cost_tracker)
    metering = MeteringEngine(InMemoryMeteringEventStore(), token_manager)
    usage = UsageEngine(metering, quotas)

    settings = TenantSettingsEngine(InMemoryTenantSettingsStore())
    invoices = InMemoryInvoiceStore()

    users = UserEngine(InMemoryUserStore())
    roles = RoleEngine(InMemoryRoleAssignmentStore())
    user = users.create(firm_id, email="partner@firm.test", display_name="Partner")
    roles.assign(firm_id, user.id, Role.PARTNER)

    return CustomerPortalEngine(
        users, roles, subs, catalog, licenses, modules, usage, settings, invoices
    )


def test_customer_portal_snapshot_aggregates_every_domain() -> None:
    portal = _customer_portal()

    snapshot = portal.snapshot("firm-1")

    assert snapshot.firm_id == "firm-1"
    assert len(snapshot.users) == 1
    assert len(snapshot.role_assignments) == 1
    assert snapshot.plan.name.value == "professional"
    assert snapshot.subscription.status.value == "active"
    assert len(snapshot.usage) > 0


def _marketplace_subscription_engine() -> tuple[MarketplaceSubscriptionEngine, LicenseEngine, str]:
    registry = InMemoryPluginRegistry()
    manifest = PluginManifest(
        id="plugin-1",
        name="Test plugin",
        version="1.0.0",
        plugin_type=PluginType.CONNECTOR,
        author="test-author",
        description="A test plugin",
        license="MIT",
        status=PublishingStatus.PUBLISHED,
    )
    registry.register(manifest)
    permissions = PermissionEngine(InMemoryPermissionStore())
    extensions = ExtensionEngine(InMemoryExtensionStore(), registry, permissions)
    marketplace = MarketplaceEngine(registry, InMemoryReviewStore(), extensions)

    licenses = LicenseEngine(
        InMemoryLicenseGrantStore(),
        InMemoryFloatingPoolStore(),
        LicenseKeySigner(secret="test-secret-0123456789abcdef"),
    )
    billing = BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        ManualPaymentGateway(),
        NoOpAccountingExport(),
    )
    engine = MarketplaceSubscriptionEngine(
        marketplace, licenses, billing, InMemoryExtensionSubscriptionStore()
    )
    return engine, licenses, manifest.id


def test_subscribe_installs_extension_and_grants_api_license() -> None:
    engine, licenses, plugin_id = _marketplace_subscription_engine()

    subscription = engine.subscribe("firm-1", plugin_id, monthly_price_usd=29.0)

    assert subscription.status.value == "active"
    active_ids = {g.id for g in licenses.active_grants_for_firm("firm-1")}
    assert subscription.license_grant_id in active_ids


def test_unsubscribe_revokes_license_and_cancels_subscription() -> None:
    engine, licenses, plugin_id = _marketplace_subscription_engine()
    subscription = engine.subscribe("firm-1", plugin_id)

    engine.unsubscribe("firm-1", plugin_id)

    active_ids = {g.id for g in licenses.active_grants_for_firm("firm-1")}
    assert subscription.license_grant_id not in active_ids
    assert engine.list_for_firm("firm-1")[0].status.value == "cancelled"
