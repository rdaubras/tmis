from datetime import UTC, datetime, timedelta

from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.monitoring_adapter import CostTrackerSummaryAdapter
from tmis.platform.cost_control.schemas import CostEntry
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


def _engine() -> CostTrackerEngine:
    return CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore())


def test_record_computes_cost_from_the_shared_estimator() -> None:
    engine = _engine()

    entry = engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000)

    assert entry.cost_usd > 0.0
    assert entry.cache_hit is False


def test_record_is_free_on_a_cache_hit() -> None:
    engine = _engine()

    entry = engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000, cache_hit=True)

    assert entry.cost_usd == 0.0


def test_cost_by_user_case_and_workflow_are_scoped_independently() -> None:
    engine = _engine()
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000, case_id="case-1")
    engine.record("firm-1", "user-2", "openai", "gpt-4o", 1000, case_id="case-2")

    assert engine.cost_by_user("user-1") > 0.0
    assert engine.cost_by_case("case-1") > 0.0
    assert engine.cost_by_case("case-2") > 0.0
    assert engine.cost_by_user("user-1") != engine.cost_by_user("user-99")


def test_cost_by_provider_filters_within_a_firm() -> None:
    engine = _engine()
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000)
    engine.record("firm-1", "user-1", "anthropic", "claude", 1000)

    openai_cost = engine.cost_by_provider("firm-1", "openai")
    anthropic_cost = engine.cost_by_provider("firm-1", "anthropic")

    assert openai_cost > 0.0
    assert anthropic_cost > 0.0


def test_total_cost_usd_sums_every_recorded_entry() -> None:
    engine = _engine()
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000)
    engine.record("firm-2", "user-2", "openai", "gpt-4o", 2000)

    assert engine.total_cost_usd() == engine.cost_by_user("user-1") + engine.cost_by_user("user-2")


def test_cache_hit_rate_reflects_recorded_hits_and_misses() -> None:
    engine = _engine()
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 100, cache_hit=True)
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 100, cache_hit=False)

    assert engine.cache_hit_rate("firm-1") == 0.5


def test_cache_hit_rate_is_zero_for_a_firm_with_no_entries() -> None:
    engine = _engine()

    assert engine.cache_hit_rate("firm-1") == 0.0


def test_check_thresholds_flags_a_breach_within_the_period() -> None:
    engine = _engine()
    engine.set_alert_threshold("firm", "firm-1", max_cost_usd=0.0001, period_days=30)
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 100_000)

    breaches = engine.check_thresholds("firm-1")

    assert len(breaches) == 1
    assert breaches[0].current_cost_usd > 0.0001


def test_check_thresholds_ignores_entries_outside_the_period() -> None:
    entry_store = InMemoryCostEntryStore()
    threshold_store = InMemoryAlertThresholdStore()
    engine = CostTrackerEngine(entry_store, threshold_store)
    engine.set_alert_threshold("firm", "firm-1", max_cost_usd=0.0, period_days=1)
    entry_store.save(
        CostEntry(
            id="stale-1",
            firm_id="firm-1",
            user_id="user-1",
            case_id=None,
            workflow_id=None,
            provider="openai",
            model="gpt-4o",
            token_count=100_000,
            cost_usd=5.0,
            cache_hit=False,
            recorded_at=datetime.now(UTC) - timedelta(days=5),
        )
    )

    breaches = engine.check_thresholds("firm-1")

    assert breaches == []


def test_cost_tracker_summary_adapter_exposes_total_cost() -> None:
    engine = _engine()
    engine.record("firm-1", "user-1", "openai", "gpt-4o", 1000)
    adapter = CostTrackerSummaryAdapter(engine)

    assert adapter.total_cost_usd() == engine.total_cost_usd()
