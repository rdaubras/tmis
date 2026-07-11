import pytest

from tmis.workflow_automation.condition_engine import (
    Comparator,
    ConditionEngine,
    UnknownExpressionError,
    cond_and,
    cond_compare,
    cond_date_after,
    cond_date_before,
    cond_not,
    cond_or,
    cond_ref,
    cond_role_is,
)
from tmis.workflow_automation.rule_engine import InMemoryRuleStore, RuleEngine


def test_condition_engine_and_or_not() -> None:
    engine = ConditionEngine()
    condition = cond_and(
        cond_role_is("avocat"),
        cond_or(cond_compare("amount", Comparator.GT, "1000"), cond_role_is("associe")),
        cond_not(cond_compare("archived", Comparator.EQ, "true")),
    )

    assert engine.evaluate(condition, {"role": "avocat", "amount": "5000", "archived": "false"})
    assert not engine.evaluate(condition, {"role": "avocat", "amount": "5000", "archived": "true"})


def test_condition_engine_numeric_and_text_comparators() -> None:
    engine = ConditionEngine()

    assert engine.evaluate(cond_compare("amount", Comparator.GT, "100"), {"amount": "200"})
    assert not engine.evaluate(cond_compare("amount", Comparator.GT, "100"), {"amount": "50"})
    assert engine.evaluate(cond_compare("status", Comparator.EQ, "actif"), {"status": "actif"})


def test_condition_engine_missing_field_is_false() -> None:
    engine = ConditionEngine()

    assert engine.evaluate(cond_compare("missing", Comparator.EQ, "x"), {}) is False


def test_condition_engine_dates() -> None:
    engine = ConditionEngine()

    assert engine.evaluate(cond_date_before("deadline", "2026-06-01"), {"deadline": "2026-01-01"})
    assert engine.evaluate(cond_date_after("deadline", "2026-01-01"), {"deadline": "2026-06-01"})
    assert not engine.evaluate(
        cond_date_before("deadline", "2026-01-01"), {"deadline": "2026-06-01"}
    )


def test_condition_engine_named_expressions_are_reusable() -> None:
    engine = ConditionEngine()
    engine.register_expression("gros-litige", cond_compare("amount", Comparator.GT, "10000"))

    assert engine.evaluate(cond_ref("gros-litige"), {"amount": "20000"})
    assert not engine.evaluate(cond_ref("gros-litige"), {"amount": "500"})


def test_condition_engine_unknown_expression_raises() -> None:
    engine = ConditionEngine()

    with pytest.raises(UnknownExpressionError):
        engine.evaluate(cond_ref("unknown"), {})


def test_rule_engine_create_and_evaluate() -> None:
    ce = ConditionEngine()
    engine = RuleEngine(InMemoryRuleStore(), ce)
    rule = engine.create_rule(
        "firm-1", "Gros dossier", cond_compare("amount", Comparator.GT, "10000")
    )

    assert engine.evaluate("firm-1", rule.id, {"amount": "20000"}) is True
    assert engine.evaluate("firm-1", rule.id, {"amount": "500"}) is False


def test_rule_engine_deactivated_rule_never_matches() -> None:
    ce = ConditionEngine()
    engine = RuleEngine(InMemoryRuleStore(), ce)
    rule = engine.create_rule(
        "firm-1", "Gros dossier", cond_compare("amount", Comparator.GT, "10000")
    )
    engine.deactivate_rule("firm-1", rule.id)

    assert engine.evaluate("firm-1", rule.id, {"amount": "999999"}) is False


def test_rule_engine_evaluate_all_returns_matching_active_rules() -> None:
    ce = ConditionEngine()
    engine = RuleEngine(InMemoryRuleStore(), ce)
    engine.create_rule("firm-1", "A", cond_compare("amount", Comparator.GT, "10000"))
    engine.create_rule("firm-1", "B", cond_compare("amount", Comparator.LT, "100"))

    matches = engine.evaluate_all("firm-1", {"amount": "20000"})

    assert [r.name for r in matches] == ["A"]


def test_rule_engine_unknown_rule_raises() -> None:
    ce = ConditionEngine()
    engine = RuleEngine(InMemoryRuleStore(), ce)

    with pytest.raises(KeyError):
        engine.get("firm-1", "unknown")
