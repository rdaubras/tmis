"""A small, serializable condition tree — AND/OR/NOT, comparators,
dates, roles, and named reusable expressions — evaluated against a
plain `context: dict[str, str]` assembled by the caller (decoupled
input, same convention as `ai_governance.confidence`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Comparator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class ConditionKind(StrEnum):
    AND = "and"
    OR = "or"
    NOT = "not"
    COMPARE = "compare"
    ROLE_IS = "role_is"
    DATE_BEFORE = "date_before"
    DATE_AFTER = "date_after"
    REF = "ref"


@dataclass(frozen=True, slots=True)
class Condition:
    kind: ConditionKind
    children: tuple[Condition, ...] = field(default_factory=tuple)
    operand: Condition | None = None
    field: str | None = None
    comparator: Comparator | None = None
    value: str | None = None
    ref_name: str | None = None


def cond_and(*children: Condition) -> Condition:
    return Condition(kind=ConditionKind.AND, children=children)


def cond_or(*children: Condition) -> Condition:
    return Condition(kind=ConditionKind.OR, children=children)


def cond_not(operand: Condition) -> Condition:
    return Condition(kind=ConditionKind.NOT, operand=operand)


def cond_compare(field_name: str, comparator: Comparator, value: str) -> Condition:
    return Condition(
        kind=ConditionKind.COMPARE, field=field_name, comparator=comparator, value=value
    )


def cond_role_is(role: str) -> Condition:
    return Condition(kind=ConditionKind.ROLE_IS, value=role)


def cond_date_before(field_name: str, value: str) -> Condition:
    return Condition(kind=ConditionKind.DATE_BEFORE, field=field_name, value=value)


def cond_date_after(field_name: str, value: str) -> Condition:
    return Condition(kind=ConditionKind.DATE_AFTER, field=field_name, value=value)


def cond_ref(name: str) -> Condition:
    return Condition(kind=ConditionKind.REF, ref_name=name)
