import asyncio

from tmis.ai_fabric.quotas.engine import QuotaEngine as AIQuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore as AIInMemoryQuotaStore
from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.store import InMemoryMeteringEventStore
from tmis.business_platform.modules.engine import ModuleRegistry
from tmis.business_platform.modules.store import InMemoryModuleActivationStore
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.store import InMemoryQuotaOverrideStore
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.usage.engine import UsageEngine
from tmis.cloud_operations.incident_management.engine import IncidentManagementEngine
from tmis.cloud_operations.incident_management.schemas import IncidentSeverity
from tmis.cloud_operations.incident_management.store import (
    InMemoryIncidentStore,
    InMemoryIncidentUpdateStore,
)
from tmis.cloud_operations.security_monitoring.engine import SecurityMonitoringEngine
from tmis.cloud_operations.tenant_monitoring.engine import TenantMonitoringEngine
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.identity_platform.security_events.schemas import LoginFailed, LoginSucceeded
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


def _tenant_stack(firm_id: str = "firm-1") -> tuple[AnalyticsEngine, UsageEngine]:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(PlanName.PROFESSIONAL)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id)

    modules = ModuleRegistry(InMemoryModuleActivationStore(), catalog, subs)
    ai_quotas = AIQuotaEngine(AIInMemoryQuotaStore())
    quotas = BusinessQuotaEngine(catalog, subs, InMemoryQuotaOverrideStore(), ai_quotas)
    cost_entries = InMemoryCostEntryStore()
    cost_tracker = CostTrackerEngine(cost_entries, InMemoryAlertThresholdStore())
    token_manager = TokenManager(cost_tracker)
    metering = MeteringEngine(InMemoryMeteringEventStore(), token_manager)
    usage = UsageEngine(metering, quotas)

    analytics = AnalyticsEngine(
        subs, catalog, PricingEngine(), usage, modules, cost_tracker, cost_entries
    )
    return analytics, usage


def test_tenant_monitoring_composes_analytics_usage_and_incidents() -> None:
    analytics, usage = _tenant_stack("firm-1")
    incidents = IncidentManagementEngine(InMemoryIncidentStore(), InMemoryIncidentUpdateStore())
    incidents.open_incident("Outage", "desc", IncidentSeverity.HIGH, firm_id="firm-1")

    engine = TenantMonitoringEngine(analytics, usage, incidents)
    snapshot = engine.snapshot("firm-1")

    assert snapshot.firm_id == "firm-1"
    assert snapshot.monthly_recurring_revenue_usd > 0
    assert snapshot.open_incidents_count == 1
    assert len(snapshot.quota_usage) > 0


def test_tenant_monitoring_reflects_zero_incidents_for_quiet_firm() -> None:
    analytics, usage = _tenant_stack("firm-2")
    incidents = IncidentManagementEngine(InMemoryIncidentStore(), InMemoryIncidentUpdateStore())

    snapshot = TenantMonitoringEngine(analytics, usage, incidents).snapshot("firm-2")
    assert snapshot.open_incidents_count == 0


def test_security_monitoring_counts_events_by_type_across_the_bus() -> None:
    bus = SecurityEventBus()
    asyncio.run(bus.publish(LoginSucceeded(firm_id="firm-1", user_id="u1", method="password")))
    asyncio.run(bus.publish(LoginFailed(firm_id="firm-1", identity="u1", reason="bad password")))
    asyncio.run(bus.publish(LoginFailed(firm_id="firm-2", identity="u2", reason="bad password")))

    overview = SecurityMonitoringEngine(bus).overview()
    assert overview.total_events == 3
    assert overview.events_by_type == {"LoginSucceeded": 1, "LoginFailed": 2}


def test_security_monitoring_overview_of_empty_bus_is_zero() -> None:
    overview = SecurityMonitoringEngine(SecurityEventBus()).overview()
    assert overview.total_events == 0
    assert overview.events_by_type == {}
