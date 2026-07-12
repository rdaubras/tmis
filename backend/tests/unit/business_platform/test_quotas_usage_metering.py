from tmis.ai_fabric.quotas.engine import QuotaEngine as AIQuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore as AIInMemoryQuotaStore
from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.schemas import MeteredDimension
from tmis.business_platform.metering.store import InMemoryMeteringEventStore
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.business_platform.quotas.store import InMemoryQuotaOverrideStore
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.usage.engine import UsageEngine
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


def _onboarded_firm(
    firm_id: str = "firm-1", plan_name: PlanName = PlanName.PROFESSIONAL
) -> tuple[BusinessQuotaEngine, MeteringEngine, UsageEngine]:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(plan_name)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id)

    ai_quotas = AIQuotaEngine(AIInMemoryQuotaStore())
    quotas = BusinessQuotaEngine(catalog, subs, InMemoryQuotaOverrideStore(), ai_quotas)

    cost_tracker = CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore())
    token_manager = TokenManager(cost_tracker)
    metering = MeteringEngine(InMemoryMeteringEventStore(), token_manager)
    usage = UsageEngine(metering, quotas)
    return quotas, metering, usage


def test_gpu_minutes_has_no_default_plan_allowance() -> None:
    quotas, _metering, _usage = _onboarded_firm()

    assert quotas.limit_for("firm-1", QuotaDimension.GPU_MINUTES) == 0


def test_quota_override_is_additive_on_top_of_plan_limit() -> None:
    quotas, _metering, _usage = _onboarded_firm()
    base_limit = quotas.limit_for("firm-1", QuotaDimension.STORAGE_GB)

    quotas.set_override("firm-1", QuotaDimension.STORAGE_GB, extra_amount=50)

    assert quotas.limit_for("firm-1", QuotaDimension.STORAGE_GB) == base_limit + 50


def test_check_ai_calls_true_when_under_limit() -> None:
    quotas, _metering, _usage = _onboarded_firm()

    assert quotas.check_ai_calls("firm-1") is True


def test_check_ai_calls_false_once_override_drives_limit_to_zero() -> None:
    quotas, _metering, _usage = _onboarded_firm()
    base_limit = quotas.limit_for("firm-1", QuotaDimension.AI_CALLS)

    quotas.set_override("firm-1", QuotaDimension.AI_CALLS, extra_amount=-base_limit)

    assert quotas.check_ai_calls("firm-1") is False


def test_metering_record_ai_call_composes_token_manager() -> None:
    _quotas, metering, _usage = _onboarded_firm()

    metering.record_ai_call(
        "firm-1", "user-1", "openai", "gpt-4o", "prompt text", "a longer response text here"
    )

    assert metering.total_for_dimension("firm-1", MeteredDimension.AI_CALLS) == 1
    assert metering.total_for_dimension("firm-1", MeteredDimension.TOKENS) > 0


def test_usage_snapshot_computes_percent_for_mapped_dimensions() -> None:
    _quotas, metering, usage = _onboarded_firm()
    metering.record(firm_id="firm-1", dimension=MeteredDimension.STORAGE_GB, quantity=10)

    snapshot = usage.snapshot("firm-1", MeteredDimension.STORAGE_GB)

    assert snapshot.used == 10
    assert snapshot.limit is not None
    assert snapshot.percent_used == 10 / snapshot.limit * 100


def test_usage_snapshot_has_no_limit_for_unmapped_dimensions() -> None:
    _quotas, metering, usage = _onboarded_firm()
    metering.record(firm_id="firm-1", dimension=MeteredDimension.SEARCHES, quantity=5)

    snapshot = usage.snapshot("firm-1", MeteredDimension.SEARCHES)

    assert snapshot.limit is None
    assert snapshot.percent_used is None
