"""Demonstrates the sprint's end-of-sprint demo journey end to end
through the bootstrap singletons: create a firm, activate a
subscription, assign licenses, execute a workflow respecting quotas,
and track consumption via usage/analytics."""

from tmis.business_platform.bootstrap import (
    get_analytics_engine,
    get_business_quota_engine,
    get_customer_portal_engine,
    get_license_engine,
    get_metering_engine,
    get_module_registry,
    get_plan_catalog,
    get_report_engine,
    get_subscription_engine,
    get_usage_engine,
)
from tmis.business_platform.licenses.schemas import LicenseType
from tmis.business_platform.metering.schemas import MeteredDimension
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.business_platform.subscriptions.schemas import SubscriptionStatus
from tmis.identity_platform.bootstrap import get_role_engine, get_user_engine
from tmis.identity_platform.roles.schemas import Role


def test_full_customer_journey_from_onboarding_to_consumption_tracking() -> None:
    firm_id = "firm-journey"

    # 1. Create the firm's first user and a partner role.
    users = get_user_engine()
    roles = get_role_engine()
    partner = users.create(firm_id, email="partner@firm.test", display_name="Partner")
    roles.assign(firm_id, partner.id, Role.PARTNER)

    # 2. Activate a subscription on the Business plan.
    catalog = get_plan_catalog()
    subs = get_subscription_engine()
    plan = catalog.latest(PlanName.BUSINESS)
    subs.start_trial(firm_id, plan.id)
    subscription = subs.activate(firm_id)
    assert subscription.status is SubscriptionStatus.ACTIVE

    # 3. Activate the workflow_automation module (granted by the Business plan).
    modules = get_module_registry()
    modules.activate(firm_id, TmisModule.WORKFLOW_AUTOMATION)
    assert modules.is_active(firm_id, TmisModule.WORKFLOW_AUTOMATION) is True

    # 4. Assign licenses to team members.
    licenses = get_license_engine()
    licenses.assign(firm_id, LicenseType.NOMINATIVE, holder_id=partner.id)
    associate_grant = licenses.assign(firm_id, LicenseType.NOMINATIVE, holder_id="associate-1")
    assert len(licenses.active_grants_for_firm(firm_id)) == 2

    # 5. Execute workflows while respecting the WORKFLOWS quota.
    quotas = get_business_quota_engine()
    metering = get_metering_engine()
    limit = quotas.limit_for(firm_id, QuotaDimension.WORKFLOWS)
    for _ in range(3):
        used = metering.total_for_dimension(firm_id, MeteredDimension.WORKFLOWS_EXECUTED)
        result = quotas.check(firm_id, QuotaDimension.WORKFLOWS, int(used))
        assert result.allowed is True
        metering.record(firm_id, MeteredDimension.WORKFLOWS_EXECUTED, 1)
    assert metering.total_for_dimension(firm_id, MeteredDimension.WORKFLOWS_EXECUTED) == 3
    assert limit > 3  # Business plan grants ample headroom

    # 6. Record some AI consumption for the analytics dashboard.
    metering.record_ai_call(
        firm_id, partner.id, "openai", "gpt-4o", "draft a clause", "here is the clause"
    )

    # 7. Track consumption via usage snapshots, analytics dashboard, and the
    #    customer portal — every figure should be internally consistent.
    usage = get_usage_engine()
    workflow_snapshot = usage.snapshot(firm_id, MeteredDimension.WORKFLOWS_EXECUTED)
    assert workflow_snapshot.used == 3

    analytics = get_analytics_engine()
    dashboard = analytics.build_dashboard(firm_id)
    assert dashboard.plan_name is PlanName.BUSINESS
    assert dashboard.total_ai_cost_usd >= 0

    portal = get_customer_portal_engine()
    snapshot = portal.snapshot(firm_id)
    assert len(snapshot.users) == 1
    assert len(snapshot.license_grants) == 2
    assert TmisModule.WORKFLOW_AUTOMATION in snapshot.active_modules

    report = get_report_engine().generate(firm_id)
    assert report.firm_id == firm_id
    assert report.sections["usage.workflows_executed"] == "3"

    # Revoking a license removes it from the active roster without
    # touching the other one.
    licenses.revoke(firm_id, associate_grant.id)
    assert len(licenses.active_grants_for_firm(firm_id)) == 1
