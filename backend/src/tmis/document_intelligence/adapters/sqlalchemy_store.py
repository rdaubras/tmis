"""Postgres-backed `DocumentStorePort` (Sprint 26 — see
docs/151-architecture-persistance.md), firm-scoped since ADR-DOCINT-01
("document_intelligence" persistent & isolated slice, see
docs/14-document-intelligence.md § Persistance & isolation multi-tenant).
Sits behind the exact same port as `InMemoryDocumentStore`
(`tmis.document_intelligence.storage.ports.DocumentStorePort`) — the
pipeline never knows which one it was given.

Reuses `tmis.core.db.base.Base` (the repo's single declarative base) and
`tmis.core.db.dataclass_json` (the shared dataclass<->JSON codec used by
every domain store this sprint) — no second persistence mechanism, no
per-domain (de)serialization code.

Versioning (see docs/09-roadmap-30-sprints.md, Sprint 26): `save()` always
INSERTs a new row, never updates one in place. Each row is one version,
linked to the previous one by `previous_version_id`. `get(document_id)`
keeps the port's existing meaning — "the" record for that id — now defined
as its latest version, scoped to the store's own firm; `list_versions()`
(not on the port, additional API surface used by the version-history
endpoint) returns the full history, also scoped.

`raw_bytes` — the uploaded file itself — lives in this table (`payload`
carries everything else). Firm-scoping every read here is what closes the
cross-tenant leak of that raw content (docs/14-document-intelligence.md §
Points de vigilance); a `document_id` belonging to another firm resolves
to `None`, never a row, so `raw_bytes` is never handed to the wrong
tenant.
"""

import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal
from tmis.core.tenancy import scoped_query
from tmis.document_intelligence.schemas.record import DocumentRecord


class DocumentRecordModel(Base):
    """One row per document *version* — see the module docstring."""

    __tablename__ = "document_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_records.id"), default=None, nullable=True
    )
    filename: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    raw_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


_EXCLUDED_FROM_PAYLOAD = ("raw_bytes", "document_id", "filename", "status")


def _record_to_row_fields(record: DocumentRecord) -> dict[str, Any]:
    full = to_json(record)
    payload = {k: v for k, v in full.items() if k not in _EXCLUDED_FROM_PAYLOAD}
    return {"raw_bytes": full["raw_bytes"], "payload": payload}


def _row_to_record(row: DocumentRecordModel) -> DocumentRecord:
    combined: dict[str, Any] = dict(row.payload)
    combined["raw_bytes"] = row.raw_bytes
    combined["document_id"] = row.document_id
    combined["filename"] = row.filename
    combined["status"] = row.status
    result: DocumentRecord = from_json(combined, DocumentRecord)
    return result


class SQLAlchemyDocumentStore:
    """Implements `DocumentStorePort` exactly (same methods, same return
    types as `InMemoryDocumentStore`) on top of the repo's single sync
    SQLAlchemy engine — see `tmis.core.db.session` for why the sync engine
    is used here (the port's methods are synchronous, so the adapter must
    be too).

    Scoped to exactly one firm for its whole lifetime (ADR-DOCINT-01,
    "document_intelligence" persistent & isolated slice, see
    docs/14-document-intelligence.md) — mirrors `SQLAlchemyCaseStore`'s
    "bind `firm_id` once, at construction" shape. Keeps the Sprint 26
    `session_factory` constructor argument rather than a request-bound
    `Session` (ADR-CASEINT-03's same reasoning applies here): this store
    is also read and written from a Celery task that has no HTTP request
    to borrow a `Session` from, only ever its own `firm_id`.
    """

    def __init__(
        self, session_factory: Callable[[], Session] = SessionLocal, *, firm_id: uuid.UUID | str
    ) -> None:
        self._session_factory = session_factory
        self._firm_id = str(firm_id)

    def save(self, record: DocumentRecord) -> None:
        with self._session_factory() as session:
            latest = session.execute(
                scoped_query(DocumentRecordModel, self._firm_id)
                .where(DocumentRecordModel.document_id == record.document_id)
                .order_by(DocumentRecordModel.version.desc())
                .limit(1)
            ).scalar_one_or_none()
            row_fields = _record_to_row_fields(record)
            row = DocumentRecordModel(
                document_id=record.document_id,
                firm_id=self._firm_id,
                version=(latest.version + 1) if latest else 1,
                previous_version_id=latest.id if latest else None,
                filename=record.filename,
                status=record.status.value,
                **row_fields,
            )
            session.add(row)
            session.commit()

    def get(self, document_id: str) -> DocumentRecord | None:
        with self._session_factory() as session:
            row = session.execute(
                scoped_query(DocumentRecordModel, self._firm_id)
                .where(DocumentRecordModel.document_id == document_id)
                .order_by(DocumentRecordModel.version.desc())
                .limit(1)
            ).scalar_one_or_none()
            return _row_to_record(row) if row is not None else None

    def list_ids(self) -> list[str]:
        with self._session_factory() as session:
            rows = session.execute(
                scoped_query(DocumentRecordModel, self._firm_id)
                .with_only_columns(DocumentRecordModel.document_id)
                .distinct()
            ).all()
            return [row[0] for row in rows]

    def list_versions(self, document_id: str) -> list[DocumentRecord]:
        """Full version history, oldest first — not part of
        `DocumentStorePort` (which only ever exposes the latest version);
        used by the version-history API endpoint (Sprint 26 Phase 4)."""
        with self._session_factory() as session:
            rows = (
                session.execute(
                    scoped_query(DocumentRecordModel, self._firm_id)
                    .where(DocumentRecordModel.document_id == document_id)
                    .order_by(DocumentRecordModel.version.asc())
                )
                .scalars()
                .all()
            )
            return [_row_to_record(row) for row in rows]


__all__ = ["DocumentRecordModel", "SQLAlchemyDocumentStore"]
