from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ConditionOperator(StrEnum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"


@dataclass(frozen=True, slots=True)
class WorkflowCondition:
    """A condition is **data**, never a code string — TMIS does not
    evaluate plugin-authored expressions (`eval`/`exec`); see
    `evaluate()` below for the fixed, closed set of operators
    supported."""

    field: str
    operator: ConditionOperator
    value: Any = None


def evaluate(condition: WorkflowCondition | None, context: dict[str, Any]) -> bool:
    if condition is None:
        return True
    present = condition.field in context
    actual = context.get(condition.field)
    match condition.operator:
        case ConditionOperator.EXISTS:
            return present
        case ConditionOperator.NOT_EXISTS:
            return not present
        case ConditionOperator.EQUALS:
            return present and actual == condition.value
        case ConditionOperator.NOT_EQUALS:
            return (not present) or actual != condition.value
        case ConditionOperator.GREATER_THAN:
            return present and isinstance(actual, int | float) and actual > condition.value
        case ConditionOperator.LESS_THAN:
            return present and isinstance(actual, int | float) and actual < condition.value
        case _:
            return False


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    id: str
    name: str
    action: str
    condition: WorkflowCondition | None = None
    on_success: str | None = None
    on_failure: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """The sprint's "WORKFLOW SDK" spec: définition des étapes,
    conditions, événements, validations, actions — exportable/
    importable (see `tmis.platform_sdk.workflow_sdk.serialization`)."""

    id: str
    name: str
    steps: tuple[WorkflowStep, ...]
    trigger_events: tuple[str, ...] = field(default_factory=tuple)
    validations: tuple[str, ...] = field(default_factory=tuple)
