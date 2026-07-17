"""Postgres-backed `DocumentStorePort` (Sprint 26 — Module Document +
Persistance, see docs/151-architecture-persistance.md; firm isolation
added in the `cases -> drafting` slice, see docs/28-legal-drafting.md
ADR-SLICE-01/02). Sits behind the exact same port as
`InMemoryDocumentStore` (`tmis.legal_drafting.documents.ports.
DocumentStorePort`) — callers never know which one they were given.

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

Unlike Sprint 26's original shape, this store is no longer constructed
around a `session_factory` that opens/closes one session per call: it now
takes the request's own `Session` plus the caller's `firm_id` at
construction (ADR-SLICE-02), mirroring `SqlAlchemyCaseRepository(session)`
— firm_id is fixed for the store's lifetime (one request), so every
method it exposes keeps `DocumentStorePort`'s original signature
(`get(document_id)`, `save(document)`, `list_ids()`); nothing above the
store needs to know isolation is happening. Every read/write is routed
through `core.tenancy.scoped_query`, which refuses to build a query
against a model without a `firm_id` column — the same guard the `cases`
table relies on. `firm_id` is stored as a plain string (like `id`/
`case_id` on this JSON-payload table) even though `Principal.firm_id` is a
`uuid.UUID` — an explicit `str(firm_id)` cast at the boundary, documented
here rather than left as a silent trap (see docs/28-legal-drafting.md
§ points de vigilance)."""

import uuid
from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.tenancy import scoped_query
from tmis.legal_drafting.documents.schemas import Document

_EXCLUDED_FROM_PAYLOAD = ("id", "case_id", "status", "firm_id")


class DraftDocumentModel(Base):
    """One row per `Document`, keyed by its own `id` — no surrogate
    primary key needed. `case_id`, `status` and `firm_id` are broken out
    as indexed columns; everything else round-trips through `payload`.
    `firm_id` is never part of `payload` — tenancy metadata never lives
    inside the domain JSON blob (ADR-SLICE-01)."""

    __tablename__ = "drafting_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
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
    """Implements `DocumentStorePort` on top of the repo's single sync
    SQLAlchemy engine, scoped to exactly one firm for its whole lifetime.
    Built fresh per request by `tmis.legal_drafting.bootstrap.
    get_document_orchestrator` — never cached, never shared between
    tenants (ADR-SLICE-02)."""

    def __init__(self, session: Session, firm_id: uuid.UUID) -> None:
        self._session = session
        self._firm_id = str(firm_id)

    def get(self, document_id: str) -> Document | None:
        stmt = scoped_query(DraftDocumentModel, self._firm_id).where(
            DraftDocumentModel.id == document_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return _row_to_document(row) if row is not None else None

    def save(self, document: Document) -> None:
        row_fields = _document_to_row_fields(document)
        row = DraftDocumentModel(
            id=document.id,
            firm_id=self._firm_id,
            case_id=document.case_id,
            status=document.status.value,
            **row_fields,
        )
        self._session.merge(row)
        self._session.commit()

    def list_ids(self) -> list[str]:
        stmt = scoped_query(DraftDocumentModel, self._firm_id)
        return [row.id for row in self._session.scalars(stmt)]


__all__ = ["DraftDocumentModel", "SQLAlchemyDraftDocumentStore"]
