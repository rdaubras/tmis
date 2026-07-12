from datetime import date

from tmis.workflow_automation.condition_engine.schemas import Comparator, Condition, ConditionKind


class UnknownExpressionError(KeyError):
    pass


class ConditionEngine:
    """Evaluates a `Condition` tree against a context dict. Named
    expressions registered via `register_expression` are reusable
    across rules/workflows without duplicating the tree — referenced
    with `ConditionKind.REF`."""

    def __init__(self) -> None:
        self._library: dict[str, Condition] = {}

    def register_expression(self, name: str, condition: Condition) -> None:
        self._library[name] = condition

    def evaluate(self, condition: Condition, context: dict[str, str]) -> bool:
        if condition.kind is ConditionKind.AND:
            return all(self.evaluate(child, context) for child in condition.children)
        if condition.kind is ConditionKind.OR:
            return any(self.evaluate(child, context) for child in condition.children)
        if condition.kind is ConditionKind.NOT:
            assert condition.operand is not None
            return not self.evaluate(condition.operand, context)
        if condition.kind is ConditionKind.COMPARE:
            return self._evaluate_compare(condition, context)
        if condition.kind is ConditionKind.ROLE_IS:
            return context.get("role") == condition.value
        if condition.kind is ConditionKind.DATE_BEFORE:
            return self._evaluate_date(condition, context, before=True)
        if condition.kind is ConditionKind.DATE_AFTER:
            return self._evaluate_date(condition, context, before=False)
        if condition.kind is ConditionKind.REF:
            assert condition.ref_name is not None
            referenced = self._library.get(condition.ref_name)
            if referenced is None:
                raise UnknownExpressionError(condition.ref_name)
            return self.evaluate(referenced, context)
        raise ValueError(f"Unhandled condition kind: {condition.kind}")

    def _evaluate_compare(self, condition: Condition, context: dict[str, str]) -> bool:
        assert condition.field is not None and condition.comparator is not None
        actual = context.get(condition.field)
        if actual is None:
            return False
        expected = condition.value or ""
        try:
            return self._compare_numeric(float(actual), float(expected), condition.comparator)
        except ValueError:
            return self._compare_text(actual, expected, condition.comparator)

    @staticmethod
    def _compare_numeric(actual: float, expected: float, comparator: Comparator) -> bool:
        if comparator is Comparator.EQ:
            return actual == expected
        if comparator is Comparator.NEQ:
            return actual != expected
        if comparator is Comparator.GT:
            return actual > expected
        if comparator is Comparator.GTE:
            return actual >= expected
        if comparator is Comparator.LT:
            return actual < expected
        if comparator is Comparator.LTE:
            return actual <= expected
        raise ValueError(f"Unhandled comparator: {comparator}")

    @staticmethod
    def _compare_text(actual: str, expected: str, comparator: Comparator) -> bool:
        if comparator is Comparator.EQ:
            return actual == expected
        if comparator is Comparator.NEQ:
            return actual != expected
        if comparator is Comparator.GT:
            return actual > expected
        if comparator is Comparator.GTE:
            return actual >= expected
        if comparator is Comparator.LT:
            return actual < expected
        if comparator is Comparator.LTE:
            return actual <= expected
        raise ValueError(f"Unhandled comparator: {comparator}")

    def _evaluate_date(
        self, condition: Condition, context: dict[str, str], *, before: bool
    ) -> bool:
        assert condition.field is not None and condition.value is not None
        actual = context.get(condition.field)
        if actual is None:
            return False
        actual_date = date.fromisoformat(actual)
        reference_date = date.fromisoformat(condition.value)
        return actual_date < reference_date if before else actual_date > reference_date
