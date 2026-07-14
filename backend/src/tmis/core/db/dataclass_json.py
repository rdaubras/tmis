"""Generic, recursive dataclass <-> JSON codec shared by every domain's
`SQLAlchemy*Store` (Sprint 26).

Every entity this sprint persists (`DocumentRecord`, `CaseProfile`,
`ResearchHistoryEntry`, `ReasoningSession`, drafting `Document`, `Workspace`,
`KnowledgeObject`) is a plain dataclass, several levels deep, made of
dataclasses/enums/datetimes/uuids/sets/frozensets/lists/tuples/dicts on top
of primitives. Rather than hand-writing seven bespoke (de)serializers, each
repeating the same recursion, this module writes it once: `to_json` turns
any such value into a JSON-safe structure; `from_json` reconstructs it from
that structure plus the original static type (dataclass field types are
read via `typing.get_type_hints`, so nested dataclasses/enums are
reconstructed automatically, not just the outermost one).
"""

import dataclasses
import types
import typing
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints


def to_json(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_json(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, set | frozenset):
        return sorted((to_json(v) for v in value), key=str)
    if isinstance(value, list | tuple):
        return [to_json(v) for v in value]
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    return value


def _optional_inner(tp: Any) -> tuple[bool, Any]:
    origin = get_origin(tp)
    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return True, args[0]
    return False, tp


def from_json(data: Any, tp: Any) -> Any:
    """Reconstructs a value of static type `tp` from JSON-safe `data` (the
    inverse of `to_json`). `tp` may be a dataclass, an `Enum`, a generic
    alias (`list[X]`, `dict[str, X]`, `set[X]`, `frozenset[X]`,
    `tuple[X, ...]`), `X | None`, or a primitive/`Any`."""
    if data is None:
        return None

    is_optional, inner = _optional_inner(tp)
    if is_optional:
        return from_json(data, inner)

    if dataclasses.is_dataclass(tp) and isinstance(tp, type):
        hints = get_type_hints(tp)
        kwargs = {name: from_json(data[name], hints[name]) for name in data if name in hints}
        return tp(**kwargs)

    if isinstance(tp, type) and issubclass(tp, Enum):
        return tp(data)

    if tp is datetime:
        return datetime.fromisoformat(data) if isinstance(data, str) else data

    if tp is uuid.UUID:
        return uuid.UUID(data) if isinstance(data, str) else data

    origin = get_origin(tp)
    if origin in (list, tuple, set, frozenset):
        args = get_args(tp)
        item_type = args[0] if args else Any
        items = [from_json(v, item_type) for v in data]
        if origin is tuple:
            return tuple(items)
        if origin is set:
            return set(items)
        if origin is frozenset:
            return frozenset(items)
        return items

    if origin is dict:
        args = get_args(tp)
        value_type = args[1] if len(args) == 2 else Any
        return {k: from_json(v, value_type) for k, v in data.items()}

    return data
