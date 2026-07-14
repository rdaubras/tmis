"""Postgres-backed `KnowledgeStorePort` (Sprint 26 — see
docs/151-architecture-persistance.md). Sits behind the exact same port as
`InMemoryKnowledgeStore` (`tmis.cabinet_knowledge.knowledge.store.
InMemoryKnowledgeStore`) — callers never know which one they were given.

Reuses `tmis.core.db.base.Base` (the repo's single declarative base) and
`tmis.core.db.dataclass_json` (the shared dataclass<->JSON codec used by
every domain store this sprint) — no second persistence mechanism, no
per-domain (de)serialization code.

One row per knowledge object, upserted on `save()` to match
`InMemoryKnowledgeStore`'s overwrite semantics (`self._objects[obj.id] =
obj`).
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType
from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal


class KnowledgeObjectModel(Base):
    """One row per knowledge object. `id`, `firm_id` and `type` get
    dedicated columns (the latter two indexed, for `list_for_firm`'s
    `firm_id`/`type_` filters); everything else is stored as one JSON
    payload."""

    __tablename__ = "knowledge_objects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


_EXCLUDED_FROM_PAYLOAD = ("id", "firm_id", "type")


def _object_to_payload(obj: KnowledgeObject) -> dict[str, Any]:
    full = to_json(obj)
    return {k: v for k, v in full.items() if k not in _EXCLUDED_FROM_PAYLOAD}


def _row_to_object(row: KnowledgeObjectModel) -> KnowledgeObject:
    combined: dict[str, Any] = dict(row.payload)
    combined["id"] = row.id
    combined["firm_id"] = row.firm_id
    combined["type"] = row.type
    result: KnowledgeObject = from_json(combined, KnowledgeObject)
    return result


class SQLAlchemyKnowledgeStore:
    """Implements `KnowledgeStorePort` exactly (same methods, same return
    types as `InMemoryKnowledgeStore`) on top of the repo's single sync
    SQLAlchemy engine — the port's methods are synchronous, so the adapter
    must be too."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def save(self, obj: KnowledgeObject) -> None:
        with self._session_factory() as session:
            row = KnowledgeObjectModel(
                id=obj.id,
                firm_id=obj.firm_id,
                type=obj.type.value,
                payload=_object_to_payload(obj),
            )
            session.merge(row)
            session.commit()

    def get(self, object_id: str) -> KnowledgeObject | None:
        with self._session_factory() as session:
            row = session.execute(
                select(KnowledgeObjectModel).where(KnowledgeObjectModel.id == object_id)
            ).scalar_one_or_none()
            return _row_to_object(row) if row is not None else None

    def list_for_firm(
        self, firm_id: str, type_: KnowledgeType | None = None
    ) -> list[KnowledgeObject]:
        with self._session_factory() as session:
            query = select(KnowledgeObjectModel).where(KnowledgeObjectModel.firm_id == firm_id)
            if type_ is not None:
                query = query.where(KnowledgeObjectModel.type == type_.value)
            rows = session.execute(query).scalars().all()
            return [_row_to_object(row) for row in rows]


__all__ = ["KnowledgeObjectModel", "SQLAlchemyKnowledgeStore"]
