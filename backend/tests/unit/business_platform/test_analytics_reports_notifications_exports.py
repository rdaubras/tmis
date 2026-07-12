import json

from tmis.ai_fabric.quotas.engine import QuotaEngine as AIQuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore as AIInMemoryQuotaStore
from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.exports.engine import ExportEngine
from tmis.business_platform.exports.schemas import ExportFormat
from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.store import InMemoryMeteringEventStore
from tmis.business_platform.modules.engine import ModuleRegistry
from tmis.business_platform.modules.store import InMemoryModuleActivationStore
from tmis.business_platform.notifications.engine import BusinessNotificationEngine
from tmis.business_platform.notifications.schemas import BusinessNotificationType
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.store import InMemoryQuotaOverrideStore
from tmis.business_platform.reports.engine import ReportEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.usage.engine import UsageEngine
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


def _analytics_engine(firm_id: str = "firm-1") -> AnalyticsEngine:
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

    for _ in range(3):
        metering.record_ai_call(firm_id, "user-1", "openai", "gpt-4o", "prompt", "a response")
    for _ in range(2):
        metering.record_ai_call(
            firm_id, "user-1", "openai", "gpt-4o", "prompt", "a response", cache_hit=True
        )

    return AnalyticsEngine(
        subs, catalog, PricingEngine(), usage, modules, cost_tracker, cost_entries
    )


def test_dashboard_reports_mrr_cost_and_cache_savings() -> None:
    analytics = _analytics_engine()

    dashboard = analytics.build_dashboard("firm-1")

    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    plan = catalog.latest(PlanName.PROFESSIONAL)
    assert dashboard.monthly_recurring_revenue_usd == plan.monthly_price_usd
    assert dashboard.total_ai_cost_usd > 0
    assert 0 < dashboard.cache_hit_rate < 1
    assert dashboard.cache_savings_usd > 0


def test_report_engine_generates_frozen_snapshot_from_dashboard() -> None:
    analytics = _analytics_engine()
    reports = ReportEngine(analytics)

    report = reports.generate("firm-1")

    assert report.firm_id == "firm-1"
    assert report.sections["plan"] == "professional"
    assert "usage.ai_calls" in report.sections


def test_export_engine_produces_csv_and_json() -> None:
    analytics = _analytics_engine()
    reports = ReportEngine(analytics)
    exports = ExportEngine()
    report = reports.generate("firm-1")

    csv_result = exports.export_report(report, ExportFormat.CSV)
    json_result = exports.export_report(report, ExportFormat.JSON)

    assert csv_result.media_type == "text/csv"
    assert json_result.media_type == "application/json"
    payload = json.loads(json_result.content)
    assert payload["headers"] == ["section", "value"]


def test_business_notification_engine_dispatches_through_collaboration_engine() -> None:
    notifications = BusinessNotificationEngine(NotificationEngine())

    sent = notifications.notify(
        "firm-1", "user-1", BusinessNotificationType.QUOTA_WARNING, {"dimension": "ai_calls"}
    )

    assert len(sent) == 1
    assert notifications.list_for_firm("firm-1")[0].type == "quota_warning"
