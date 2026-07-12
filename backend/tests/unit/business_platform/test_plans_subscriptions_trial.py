from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanLimits, PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.schemas import BillingCycle, SubscriptionStatus
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.business_platform.trial.engine import TrialEngine


def _catalog() -> PlanCatalog:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    return catalog


def test_seed_default_catalog_publishes_five_plans() -> None:
    catalog = _catalog()
    current = catalog.list_current_catalog()

    assert {plan.name for plan in current} == set(PlanName)


def test_publishing_new_version_never_mutates_previous() -> None:
    catalog = _catalog()
    v1 = catalog.latest(PlanName.PROFESSIONAL)

    v2 = catalog.publish(
        PlanName.PROFESSIONAL,
        PlanLimits(
            max_users=999,
            max_storage_gb=1.0,
            max_ai_calls_per_month=1,
            max_cases=1,
            max_workflows=1,
            max_agents=1,
        ),
    )

    assert v2.version == v1.version + 1
    assert catalog.get(v1.id).limits.max_users != 999


def test_subscription_pins_exact_plan_version_sold() -> None:
    catalog = _catalog()
    plans = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    v1 = catalog.latest(PlanName.BASIC)
    subscription = plans.start_trial("firm-1", v1.id)

    catalog.publish(
        PlanName.BASIC,
        PlanLimits(
            max_users=1,
            max_storage_gb=1.0,
            max_ai_calls_per_month=1,
            max_cases=1,
            max_workflows=1,
            max_agents=1,
        ),
    )

    assert plans.get("firm-1").plan_id == subscription.plan_id == v1.id


def test_activate_sets_active_status_and_period_end() -> None:
    catalog = _catalog()
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(PlanName.BASIC)
    subs.start_trial("firm-1", plan.id)

    subscription = subs.activate("firm-1", BillingCycle.ANNUAL)

    assert subscription.status is SubscriptionStatus.ACTIVE
    assert subscription.billing_cycle is BillingCycle.ANNUAL
    assert subscription.current_period_end is not None


def test_advance_period_persists_new_period_end() -> None:
    catalog = _catalog()
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(PlanName.BASIC)
    subs.start_trial("firm-1", plan.id)
    subs.activate("firm-1")
    first_period_end = subs.get("firm-1").current_period_end

    subs.advance_period("firm-1")

    assert subs.get("firm-1").current_period_end != first_period_end


def test_trial_engine_extend_pushes_trial_end_later() -> None:
    catalog = _catalog()
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    trial = TrialEngine(subs)
    plan = catalog.latest(PlanName.TRIAL)
    trial.start("firm-1", plan.id)
    before = subs.get("firm-1").trial_ends_at

    trial.extend("firm-1", extra_days=30)

    after = subs.get("firm-1").trial_ends_at
    assert after is not None and before is not None
    assert after > before


def test_trial_engine_convert_to_paid_activates_subscription() -> None:
    catalog = _catalog()
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    trial = TrialEngine(subs)
    plan = catalog.latest(PlanName.TRIAL)
    trial.start("firm-1", plan.id)

    subscription = trial.convert_to_paid("firm-1")

    assert subscription.status is SubscriptionStatus.ACTIVE
