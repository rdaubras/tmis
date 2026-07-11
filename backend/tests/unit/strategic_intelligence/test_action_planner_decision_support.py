import pytest

from tmis.strategic_intelligence.action_planner.engine import ActionPlannerEngine
from tmis.strategic_intelligence.action_planner.store import InMemoryActionPlanStore
from tmis.strategic_intelligence.decision_support.engine import DecisionSupportEngine
from tmis.strategic_intelligence.decision_support.schemas import StrategyMetrics


def test_action_planner_add_step_assigns_incrementing_order() -> None:
    engine = ActionPlannerEngine(InMemoryActionPlanStore())

    s1 = engine.add_step("firm-1", "strategy-1", "Étape 1", "procédure")
    s2 = engine.add_step("firm-1", "strategy-1", "Étape 2", "preuve")

    assert s1.order == 0
    assert s2.order == 1


def test_action_planner_reorder_updates_order_field() -> None:
    engine = ActionPlannerEngine(InMemoryActionPlanStore())
    s1 = engine.add_step("firm-1", "strategy-1", "Étape 1", "procédure")
    s2 = engine.add_step("firm-1", "strategy-1", "Étape 2", "preuve")

    engine.reorder("firm-1", "strategy-1", (s2.id, s1.id))

    steps = engine.list_for_strategy("firm-1", "strategy-1")
    assert [s.id for s in steps] == [s2.id, s1.id]


def test_action_planner_mark_done_and_remove() -> None:
    engine = ActionPlannerEngine(InMemoryActionPlanStore())
    step = engine.add_step("firm-1", "strategy-1", "Étape 1", "procédure")

    engine.mark_done("firm-1", step.id)
    assert engine.list_for_strategy("firm-1", "strategy-1")[0].done is True

    engine.remove_step("firm-1", step.id)
    assert engine.list_for_strategy("firm-1", "strategy-1") == []


def test_action_planner_mark_done_unknown_step_raises() -> None:
    engine = ActionPlannerEngine(InMemoryActionPlanStore())

    with pytest.raises(KeyError):
        engine.mark_done("firm-1", "unknown")


def test_action_planner_reorder_rejects_step_from_other_strategy() -> None:
    engine = ActionPlannerEngine(InMemoryActionPlanStore())
    step = engine.add_step("firm-1", "strategy-1", "Étape 1", "procédure")

    with pytest.raises(KeyError):
        engine.reorder("firm-1", "strategy-2", (step.id,))


def test_decision_support_never_ranks_or_recommends() -> None:
    engine = DecisionSupportEngine()

    comparison = engine.compare(
        [
            StrategyMetrics("strategy-1", "Négociation amiable", 0.6, 0.7, 0.3, 0.4, 30),
            StrategyMetrics("strategy-2", "Action prud'homale", 0.5, 0.9, 0.6, 0.8, 365),
        ]
    )

    assert len(comparison.metrics) == 2
    assert not hasattr(comparison, "recommended")
    assert not hasattr(comparison, "best_strategy_id")
    assert comparison.disclaimer
