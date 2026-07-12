import pytest

from tmis.business_platform.feature_flags.engine import BusinessFeatureFlagEngine
from tmis.business_platform.feature_flags.schemas import (
    BusinessFlagContext,
    BusinessFlagExtras,
    Environment,
)
from tmis.business_platform.feature_flags.store import InMemoryBusinessFlagExtrasStore
from tmis.business_platform.modules.engine import ModuleNotAvailableError, ModuleRegistry
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.modules.store import InMemoryModuleActivationStore
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.tenant_settings.engine import TenantSettingsEngine
from tmis.business_platform.tenant_settings.schemas import InvoicingLanguage
from tmis.business_platform.tenant_settings.store import InMemoryTenantSettingsStore
from tmis.platform.feature_flags.engine import FeatureFlagEngine
from tmis.platform.feature_flags.schemas import FeatureFlag
from tmis.platform.feature_flags.store import InMemoryFeatureFlagStore


def _onboarded_firm(
    firm_id: str = "firm-1", plan_name: PlanName = PlanName.BASIC
) -> tuple[PlanCatalog, SubscriptionEngine]:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(plan_name)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id)
    return catalog, subs


def test_module_available_only_when_plan_feature_includes_it() -> None:
    catalog, subs = _onboarded_firm(plan_name=PlanName.BASIC)
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    assert modules.is_available("firm-1", TmisModule.WORKFLOW_AUTOMATION) is False


def test_module_available_on_a_higher_tier_plan() -> None:
    catalog, subs = _onboarded_firm(plan_name=PlanName.BUSINESS)
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    assert modules.is_available("firm-1", TmisModule.WORKFLOW_AUTOMATION) is True


def test_activate_raises_when_plan_does_not_grant_the_module() -> None:
    catalog, subs = _onboarded_firm(plan_name=PlanName.BASIC)
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    with pytest.raises(ModuleNotAvailableError):
        modules.activate("firm-1", TmisModule.WORKFLOW_AUTOMATION)


def test_foundational_module_always_available() -> None:
    catalog, subs = _onboarded_firm(plan_name=PlanName.BASIC)
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    assert modules.is_available("firm-1", TmisModule.CABINET_KNOWLEDGE) is True


def test_explicit_deactivation_overrides_plan_default() -> None:
    catalog, subs = _onboarded_firm(plan_name=PlanName.BUSINESS)
    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)

    modules.deactivate("firm-1", TmisModule.WORKFLOW_AUTOMATION)

    assert modules.is_active("firm-1", TmisModule.WORKFLOW_AUTOMATION) is False
    assert modules.is_available("firm-1", TmisModule.WORKFLOW_AUTOMATION) is True


def test_business_flag_falls_back_to_base_engine_when_disabled() -> None:
    base = FeatureFlagEngine(InMemoryFeatureFlagStore())
    flags = BusinessFeatureFlagEngine(base, InMemoryBusinessFlagExtrasStore())

    assert flags.is_enabled("unknown-key", BusinessFlagContext(firm_id="firm-1")) is False


def test_business_flag_environment_extras_restrict_a_base_enabled_flag() -> None:
    base = FeatureFlagEngine(InMemoryFeatureFlagStore())
    base.set_flag(FeatureFlag(key="beta", enabled=True, enabled_firm_ids=frozenset({"firm-1"})))
    flags = BusinessFeatureFlagEngine(base, InMemoryBusinessFlagExtrasStore())
    flags.set_extras(
        BusinessFlagExtras(key="beta", enabled_environments=frozenset({Environment.STAGING}))
    )

    prod_context = BusinessFlagContext(firm_id="firm-1", environment=Environment.PRODUCTION)
    staging_context = BusinessFlagContext(firm_id="firm-1", environment=Environment.STAGING)

    assert flags.is_enabled("beta", prod_context) is False
    assert flags.is_enabled("beta", staging_context) is True


def test_tenant_settings_defaults_and_update() -> None:
    settings = TenantSettingsEngine(InMemoryTenantSettingsStore())

    defaults = settings.get_or_default("firm-1")
    assert defaults.currency == "EUR"

    updated = settings.update("firm-1", currency="USD", invoicing_language=InvoicingLanguage.EN)

    assert updated.currency == "USD"
    assert updated.invoicing_language is InvoicingLanguage.EN
