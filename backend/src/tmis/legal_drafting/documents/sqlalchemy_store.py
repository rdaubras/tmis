"""Postgres-backed `DocumentStorePort` (Sprint 26 — Module Document +
Persistance, see docs/151-architecture-persistance.md). Sits behind the
exact same port as `InMemoryDocumentStore`
(`tmis.legal_drafting.documents.ports.DocumentStorePort`) — callers never
know which one they were given.

Reuses `tmis.core.db.base.Base` (the repo's single declarative base) and
`tmis.core.db.dataclass_json` (the shared dataclass<->JSON codec used by
every domain store this sprint) — no second persistence mechanism, no
per-domain (de)serialization code.

`save()` is a plain upsert-by-id, matching `InMemoryDocumentStore`'s
`self._documents[document.id] = document` (an overwrite, never an
append) — this domain has no versioning concept on its port.

Note: `Document.is_draft` is a read-only computed `@property` (always
`True`) — not a dataclass field, so it is never part of `payload` and is
never passed back into `Document(...)` on reconstruction; it simply
recomputes to `True` on every access, as designed.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal
from tmis.legal_drafting.documents.schemas import Document

_EXCLUDED_FROM_PAYLOAD = ("id", "case_id", "status")


class DraftDocumentModel(Base):
    """One row per `Document`, keyed by its own `id` — no surrogate
    primary key needed. `case_id` and `status` are broken out as
    indexed columns because they are the two fields the drafting API
    filters/lists by; everything else round-trips through `payload`."""

    __tablename__ = "drafting_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


def _document_to_row_fields(document: Document) -> dict[str, Any]:
    full = to_json(document)
    payload = {k: v for k, v in full.items() if k not in _EXCLUDED_FROM_PAYLOAD}
    return {"payload": payload}


def _row_to_document(row: DraftDocumentModel) -> Document:
    combined: dict[str, Any] = dict(row.payload)
    combined["id"] = row.id
    combined["case_id"] = row.case_id
    combined["status"] = row.status
    result: Document = from_json(combined, Document)
    return result


class SQLAlchemyDraftDocumentStore:
    """Implements `DocumentStorePort` exactly (same methods, same return
    types as `InMemoryDocumentStore`) on top of the repo's single sync
    SQLAlchemy engine — see `tmis.core.db.session` for why the sync
    engine is used here (the port's methods are synchronous, so the
    adapter must be too)."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def get(self, document_id: str) -> Document | None:
        with self._session_factory() as session:
            row = session.execute(
                select(DraftDocumentModel).where(DraftDocumentModel.id == document_id)
            ).scalar_one_or_none()
            return _row_to_document(row) if row is not None else None

    def save(self, document: Document) -> None:
        with self._session_factory() as session:
            row_fields = _document_to_row_fields(document)
            row = DraftDocumentModel(
                id=document.id,
                case_id=document.case_id,
                status=document.status.value,
                **row_fields,
            )
            session.merge(row)
            session.commit()

    def list_ids(self) -> list[str]:
        with self._session_factory() as session:
            rows = session.execute(select(DraftDocumentModel.id)).all()
            return [row[0] for row in rows]


__all__ = ["DraftDocumentModel", "SQLAlchemyDraftDocumentStore"]
