import pytest

from tmis.cabinet_os.subscriptions.schemas import PlanTier
from tmis.platform.feature_flags.engine import FeatureFlagEngine
from tmis.platform.feature_flags.schemas import FeatureFlag, FlagEvaluationContext
from tmis.platform.feature_flags.store import InMemoryFeatureFlagStore


def _engine() -> tuple[FeatureFlagEngine, InMemoryFeatureFlagStore]:
    store = InMemoryFeatureFlagStore()
    return FeatureFlagEngine(store), store


def test_unknown_flag_is_disabled_by_default() -> None:
    engine, _ = _engine()

    assert engine.is_enabled("never-registered", FlagEvaluationContext(firm_id="firm-1")) is False


def test_kill_switch_disables_the_flag_for_everyone() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="new-ui", enabled=False, rollout_percentage=100.0))

    assert engine.is_enabled("new-ui", FlagEvaluationContext(firm_id="firm-1")) is False


def test_explicit_firm_allow_list_wins_regardless_of_rollout() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="beta", enabled_firm_ids=frozenset({"firm-1"})))

    assert engine.is_enabled("beta", FlagEvaluationContext(firm_id="firm-1")) is True
    assert engine.is_enabled("beta", FlagEvaluationContext(firm_id="firm-2")) is False


def test_explicit_user_allow_list() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="beta", enabled_user_ids=frozenset({"user-1"})))

    assert engine.is_enabled("beta", FlagEvaluationContext(user_id="user-1")) is True
    assert engine.is_enabled("beta", FlagEvaluationContext(user_id="user-2")) is False


def test_plan_allow_list() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="enterprise-only", enabled_plans=frozenset({PlanTier.ENTERPRISE})))

    assert (
        engine.is_enabled("enterprise-only", FlagEvaluationContext(plan=PlanTier.ENTERPRISE))
        is True
    )
    assert engine.is_enabled("enterprise-only", FlagEvaluationContext(plan=PlanTier.SOLO)) is False


def test_rollout_percentage_100_enables_everyone() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="ramp", rollout_percentage=100.0))

    for i in range(20):
        assert engine.is_enabled("ramp", FlagEvaluationContext(user_id=f"user-{i}")) is True


def test_rollout_percentage_0_enables_no_one_without_an_allow_list() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="ramp", rollout_percentage=0.0))

    for i in range(20):
        assert engine.is_enabled("ramp", FlagEvaluationContext(user_id=f"user-{i}")) is False


def test_rollout_bucketing_is_deterministic_across_calls() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="ramp", rollout_percentage=50.0))
    context = FlagEvaluationContext(user_id="user-42")

    first = engine.is_enabled("ramp", context)
    second = engine.is_enabled("ramp", context)

    assert first == second


def test_rollout_falls_back_to_firm_id_when_no_user_id_is_present() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="ramp", rollout_percentage=100.0))

    assert engine.is_enabled("ramp", FlagEvaluationContext(firm_id="firm-1")) is True


def test_rollout_denies_when_no_subject_id_is_available() -> None:
    engine, store = _engine()
    store.save(FeatureFlag(key="ramp", rollout_percentage=100.0))

    assert engine.is_enabled("ramp", FlagEvaluationContext()) is False


def test_feature_flag_rejects_out_of_range_rollout_percentage() -> None:
    with pytest.raises(ValueError):
        FeatureFlag(key="bad", rollout_percentage=150.0)


def test_set_flag_persists_via_the_engine() -> None:
    engine, store = _engine()

    engine.set_flag(FeatureFlag(key="via-engine", enabled_firm_ids=frozenset({"firm-1"})))

    assert store.get("via-engine") is not None
    assert engine.is_enabled("via-engine", FlagEvaluationContext(firm_id="firm-1")) is True
