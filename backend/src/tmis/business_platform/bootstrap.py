from functools import lru_cache

from tmis.ai_fabric.bootstrap import get_quota_engine as get_ai_fabric_quota_engine
from tmis.ai_fabric.bootstrap import get_token_manager
from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.billing.engine import SubscriptionBillingEngine
from tmis.business_platform.customer_portal.engine import CustomerPortalEngine
from tmis.business_platform.exports.engine import ExportEngine
from tmis.business_platform.feature_flags.engine import BusinessFeatureFlagEngine
from tmis.business_platform.feature_flags.store import InMemoryBusinessFlagExtrasStore
from tmis.business_platform.invoicing.engine import InvoicingEngine
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
from tmis.business_platform.notifications.engine import BusinessNotificationEngine
from tmis.business_platform.payments.engine import PaymentEngine
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.store import InMemoryQuotaOverrideStore
from tmis.business_platform.reports.engine import ReportEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.tenant_settings.engine import TenantSettingsEngine
from tmis.business_platform.tenant_settings.store import InMemoryTenantSettingsStore
from tmis.business_platform.trial.engine import TrialEngine
from tmis.business_platform.usage.engine import UsageEngine
from tmis.cabinet_os.bootstrap import get_billing_engine, get_invoice_store
from tmis.collaboration.bootstrap import get_notification_engine
from tmis.identity_platform.bootstrap import get_role_engine, get_user_engine
from tmis.platform.cost_control.bootstrap import get_cost_entry_store, get_cost_tracker_engine
from tmis.platform.feature_flags.bootstrap import get_feature_flag_engine
from tmis.platform.feature_flags.schemas import FeatureFlag
from tmis.platform.licensing.bootstrap import get_license_key_signer
from tmis.platform_sdk.bootstrap import get_marketplace_engine


@lru_cache
def get_plan_catalog() -> PlanCatalog:
    """Process-wide composition root for `tmis.business_platform` —
    the SaaS Business Platform (see
    docs/111-architecture-business-platform.md). Seeded once with the
    five default plans (Trial/Basic/Professional/Business/Enterprise)
    so subscriptions have something real to reference immediately."""
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    return catalog


@lru_cache
def get_subscription_engine() -> SubscriptionEngine:
    return SubscriptionEngine(InMemorySubscriptionStore(), get_plan_catalog())


@lru_cache
def get_trial_engine() -> TrialEngine:
    return TrialEngine(get_subscription_engine())


@lru_cache
def get_pricing_engine() -> PricingEngine:
    return PricingEngine()


@lru_cache
def get_subscription_billing_engine() -> SubscriptionBillingEngine:
    """Composes `cabinet_os.billing.BillingEngine` (Sprint 9) — the
    same singleton `cabinet_os` uses for client invoicing — so a
    firm's SaaS subscription invoices and its own clients' invoices
    live in one payment-provider-agnostic ledger."""
    return SubscriptionBillingEngine(
        get_billing_engine(), get_subscription_engine(), get_plan_catalog(), get_pricing_engine()
    )


@lru_cache
def get_invoicing_engine() -> InvoicingEngine:
    return InvoicingEngine(get_subscription_billing_engine(), get_subscription_engine())


@lru_cache
def get_payment_engine() -> PaymentEngine:
    return PaymentEngine(get_billing_engine())


@lru_cache
def get_license_engine() -> LicenseEngine:
    """Composes `platform.licensing.signing.LicenseKeySigner` (Sprint
    10) — the same signer `platform.licensing.LicenseEngine` uses —
    so every signed key in the system, firm-level or per-holder, uses
    the same key material."""
    return LicenseEngine(
        InMemoryLicenseGrantStore(), InMemoryFloatingPoolStore(), get_license_key_signer()
    )


@lru_cache
def get_business_quota_engine() -> BusinessQuotaEngine:
    return BusinessQuotaEngine(
        get_plan_catalog(),
        get_subscription_engine(),
        InMemoryQuotaOverrideStore(),
        get_ai_fabric_quota_engine(),
    )


@lru_cache
def get_metering_engine() -> MeteringEngine:
    return MeteringEngine(InMemoryMeteringEventStore(), get_token_manager())


@lru_cache
def get_usage_engine() -> UsageEngine:
    return UsageEngine(get_metering_engine(), get_business_quota_engine())


CABINET_KNOWLEDGE_QUALITY_FLAG_KEY = "cabinet_knowledge.quality_evaluation"
"""Feature flag key gating `cabinet_knowledge`'s AI quality-evaluation
endpoint (see `cabinet_knowledge.api.routes.evaluate_quality`) —
seeded fully open below so migrating an existing endpoint behind a
flag never breaks an existing caller; an admin can later restrict it
per firm/plan/environment/experiment without a code change."""


@lru_cache
def get_business_feature_flag_engine() -> BusinessFeatureFlagEngine:
    base = get_feature_flag_engine()
    base.set_flag(
        FeatureFlag(key=CABINET_KNOWLEDGE_QUALITY_FLAG_KEY, enabled=True, rollout_percentage=100.0)
    )
    return BusinessFeatureFlagEngine(base, InMemoryBusinessFlagExtrasStore())


@lru_cache
def get_module_registry() -> ModuleRegistry:
    return ModuleRegistry(
        InMemoryModuleActivationStore(), get_plan_catalog(), get_subscription_engine()
    )


@lru_cache
def get_tenant_settings_engine() -> TenantSettingsEngine:
    return TenantSettingsEngine(InMemoryTenantSettingsStore())


@lru_cache
def get_customer_portal_engine() -> CustomerPortalEngine:
    return CustomerPortalEngine(
        get_user_engine(),
        get_role_engine(),
        get_subscription_engine(),
        get_plan_catalog(),
        get_license_engine(),
        get_module_registry(),
        get_usage_engine(),
        get_tenant_settings_engine(),
        get_invoice_store(),
    )


@lru_cache
def get_marketplace_subscription_engine() -> MarketplaceSubscriptionEngine:
    return MarketplaceSubscriptionEngine(
        get_marketplace_engine(),
        get_license_engine(),
        get_billing_engine(),
        InMemoryExtensionSubscriptionStore(),
    )


@lru_cache
def get_analytics_engine() -> AnalyticsEngine:
    return AnalyticsEngine(
        get_subscription_engine(),
        get_plan_catalog(),
        get_pricing_engine(),
        get_usage_engine(),
        get_module_registry(),
        get_cost_tracker_engine(),
        get_cost_entry_store(),
    )


@lru_cache
def get_report_engine() -> ReportEngine:
    return ReportEngine(get_analytics_engine())


@lru_cache
def get_export_engine() -> ExportEngine:
    return ExportEngine()


@lru_cache
def get_business_notification_engine() -> BusinessNotificationEngine:
    return BusinessNotificationEngine(get_notification_engine())
