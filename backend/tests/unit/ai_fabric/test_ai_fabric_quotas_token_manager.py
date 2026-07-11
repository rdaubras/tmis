from tmis.ai_fabric.quotas.engine import QuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore
from tmis.ai_fabric.token_manager.engine import TokenManager, estimate_tokens
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore

FIRM = "firm-a"


def test_quota_check_is_true_with_no_quota_configured() -> None:
    engine = QuotaEngine(InMemoryQuotaStore())

    assert engine.check("firm", FIRM) is True


def test_quota_check_becomes_false_once_limit_reached() -> None:
    engine = QuotaEngine(InMemoryQuotaStore())
    engine.set_quota("firm", FIRM, max_calls_per_period=2, period_days=1)

    assert engine.check("firm", FIRM) is True
    engine.record_call("firm", FIRM)
    assert engine.check("firm", FIRM) is True
    engine.record_call("firm", FIRM)
    assert engine.check("firm", FIRM) is False


def test_quota_is_scoped_independently_per_scope_id() -> None:
    engine = QuotaEngine(InMemoryQuotaStore())
    engine.set_quota("firm", "firm-a", max_calls_per_period=1, period_days=1)
    engine.record_call("firm", "firm-a")

    assert engine.check("firm", "firm-a") is False
    assert engine.check("firm", "firm-b") is True


def test_estimate_tokens_is_at_least_one() -> None:
    assert estimate_tokens("") == 1
    assert estimate_tokens("un deux trois") == 3


def _token_manager() -> TokenManager:
    return TokenManager(CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore()))


def test_record_usage_returns_a_cost_entry_with_estimated_tokens() -> None:
    manager = _token_manager()

    entry = manager.record_usage(FIRM, "user-1", "openai", "gpt-x", "bonjour le monde", "salut")

    assert entry.firm_id == FIRM
    assert entry.token_count == estimate_tokens("bonjour le monde") + estimate_tokens("salut")


def test_record_usage_with_cache_hit_has_zero_cost() -> None:
    manager = _token_manager()

    entry = manager.record_usage(
        FIRM, "user-1", "openai", "gpt-x", "prompt", "réponse", cache_hit=True
    )

    assert entry.cost_usd == 0.0


def test_consumption_by_workflow_sums_workflow_entries() -> None:
    manager = _token_manager()
    manager.record_usage(
        FIRM, "user-1", "openai", "gpt-x", "prompt", "réponse", workflow_id="wf-1"
    )

    assert manager.consumption_by_workflow("wf-1") > 0.0


def test_cache_hit_rate_reflects_recorded_entries() -> None:
    manager = _token_manager()
    manager.record_usage(FIRM, "user-1", "openai", "gpt-x", "a", "b", cache_hit=True)
    manager.record_usage(FIRM, "user-1", "openai", "gpt-x", "c", "d", cache_hit=False)

    assert manager.cache_hit_rate(FIRM) == 0.5
