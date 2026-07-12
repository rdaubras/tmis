"""Confirms two firms' subscriptions, quotas, licenses and usage never
leak into each other through the process-wide bootstrap singletons —
the same multi-tenant isolation discipline established since Sprint
10 (`tmis.platform.security.tenant_isolation`)."""

from tmis.business_platform.bootstrap import (
    get_license_engine,
    get_metering_engine,
    get_module_registry,
    get_plan_catalog,
    get_subscription_engine,
    get_usage_engine,
)
from tmis.business_platform.licenses.schemas import LicenseType
from tmis.business_platform.metering.schemas import MeteredDimension
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.plans.schemas import PlanName


def test_subscriptions_and_quotas_are_isolated_per_firm() -> None:
    catalog = get_plan_catalog()
    subs = get_subscription_engine()
    firm_a, firm_b = "firm-isolation-a", "firm-isolation-b"

    basic = catalog.latest(PlanName.BASIC)
    enterprise = catalog.latest(PlanName.ENTERPRISE)
    subs.start_trial(firm_a, basic.id)
    subs.activate(firm_a)
    subs.start_trial(firm_b, enterprise.id)
    subs.activate(firm_b)

    assert subs.get(firm_a).plan_id == basic.id
    assert subs.get(firm_b).plan_id == enterprise.id

    modules = get_module_registry()
    assert modules.is_available(firm_a, TmisModule.INTEGRATION_HUB) is False
    assert modules.is_available(firm_b, TmisModule.INTEGRATION_HUB) is True


def test_licenses_are_isolated_per_firm() -> None:
    licenses = get_license_engine()
    firm_a, firm_b = "firm-isolation-lic-a", "firm-isolation-lic-b"

    licenses.assign(firm_a, LicenseType.NOMINATIVE, holder_id="user-a")
    licenses.assign(firm_b, LicenseType.NOMINATIVE, holder_id="user-b")
    licenses.assign(firm_b, LicenseType.NOMINATIVE, holder_id="user-b-2")

    assert len(licenses.active_grants_for_firm(firm_a)) == 1
    assert len(licenses.active_grants_for_firm(firm_b)) == 2


def test_usage_metering_is_isolated_per_firm() -> None:
    catalog = get_plan_catalog()
    subs = get_subscription_engine()
    metering = get_metering_engine()
    usage = get_usage_engine()
    firm_a, firm_b = "firm-isolation-usage-a", "firm-isolation-usage-b"

    plan = catalog.latest(PlanName.PROFESSIONAL)
    for firm_id in (firm_a, firm_b):
        subs.start_trial(firm_id, plan.id)
        subs.activate(firm_id)

    metering.record(firm_id=firm_a, dimension=MeteredDimension.STORAGE_GB, quantity=10)
    metering.record(firm_id=firm_b, dimension=MeteredDimension.STORAGE_GB, quantity=90)

    snapshot_a = usage.snapshot(firm_a, MeteredDimension.STORAGE_GB)
    snapshot_b = usage.snapshot(firm_b, MeteredDimension.STORAGE_GB)

    assert snapshot_a.used == 10
    assert snapshot_b.used == 90
