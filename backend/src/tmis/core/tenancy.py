"""Tenant isolation guard for multi-tenant persistence models.

`scoped_query` is the one call every repository should use to start a
query against a multi-tenant model. It does two things a plain
`select(Model).where(Model.firm_id == firm_id)` doesn't: it fails loudly
(`TypeError`, at call time) if `Model` has no `firm_id` column at all, so
a repository written against the wrong model — or a future model that
forgets to declare `firm_id` — cannot silently return cross-tenant rows.
See docs/07-strategie-securite.md (isolation multi-tenant) and T7 of the
security sprint this was added for.
"""

from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


def scoped_query(model: type[ModelT], firm_id: Any) -> Select[tuple[ModelT]]:
    if "firm_id" not in model.__mapper__.columns:
        raise TypeError(
            f"{model.__name__} has no firm_id column: refusing to build a "
            "tenant-scoped query against a model the isolation guard doesn't "
            "recognise as multi-tenant."
        )
    return select(model).where(model.firm_id == firm_id)
