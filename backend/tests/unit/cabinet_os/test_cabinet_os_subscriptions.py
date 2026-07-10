import pytest

from tmis.cabinet_os.subscriptions.engine import ConfigurableSubscriptionEngine
from tmis.cabinet_os.subscriptions.schemas import PlanTier, SubscriptionStatus
from tmis.cabinet_os.subscriptions.store import InMemorySubscriptionStore, InMemoryUsageStore


def _engine() -> ConfigurableSubscriptionEngine:
    return ConfigurableSubscriptionEngine(InMemorySubscriptionStore(), InMemoryUsageStore())


def test_subscribe_starts_in_trial_with_plan_quota() -> None:
    engine = _engine()
    subscription = engine.subscribe("firm-1", PlanTier.SOLO)

    assert subscription.status is SubscriptionStatus.TRIAL
    assert subscription.quota.max_users == 1


def test_solo_cabinet_enterprise_have_increasing_quotas() -> None:
    engine = _engine()
    solo = engine.subscribe("firm-1", PlanTier.SOLO)
    cabinet = engine.subscribe("firm-2", PlanTier.CABINET)
    enterprise = engine.subscribe("firm-3", PlanTier.ENTERPRISE)

    assert solo.quota.max_users < cabinet.quota.max_users < enterprise.quota.max_users
    assert solo.quota.max_ai_requests_per_month < enterprise.quota.max_ai_requests_per_month


def test_change_plan_updates_quota() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    upgraded = engine.change_plan("firm-1", PlanTier.CABINET)

    assert upgraded.plan is PlanTier.CABINET
    assert upgraded.quota.max_users == 25


def test_cancel_sets_status_cancelled() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    cancelled = engine.cancel("firm-1")

    assert cancelled.status is SubscriptionStatus.CANCELLED


def test_get_unknown_firm_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="No subscription"):
        engine.get("firm-1")


def test_record_ai_usage_accumulates() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    engine.record_ai_usage("firm-1", 10)
    usage = engine.record_ai_usage("firm-1", 5)

    assert usage.ai_requests_used == 15


def test_record_storage_usage_accumulates() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    usage = engine.record_storage_usage("firm-1", 2.5)

    assert usage.storage_gb_used == 2.5


def test_has_capacity_true_below_quota() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)
    engine.record_ai_usage("firm-1", 10)

    assert engine.has_capacity("firm-1", "ai_requests") is True


def test_has_capacity_false_at_or_above_quota() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)
    engine.record_ai_usage("firm-1", 500)

    assert engine.has_capacity("firm-1", "ai_requests") is False


def test_has_capacity_unknown_dimension_raises() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    with pytest.raises(ValueError, match="Unknown quota dimension"):
        engine.has_capacity("firm-1", "bananas")


def test_set_active_users_and_users_capacity() -> None:
    engine = _engine()
    engine.subscribe("firm-1", PlanTier.SOLO)

    engine.set_active_users("firm-1", 1)

    assert engine.has_capacity("firm-1", "users") is False


def test_custom_quota_map_overrides_defaults() -> None:
    from tmis.cabinet_os.subscriptions.schemas import Quota

    custom = {PlanTier.SOLO: Quota(max_users=99, max_ai_requests_per_month=1, max_storage_gb=1.0)}
    engine = ConfigurableSubscriptionEngine(
        InMemorySubscriptionStore(), InMemoryUsageStore(), quotas=custom
    )

    subscription = engine.subscribe("firm-1", PlanTier.SOLO)

    assert subscription.quota.max_users == 99
