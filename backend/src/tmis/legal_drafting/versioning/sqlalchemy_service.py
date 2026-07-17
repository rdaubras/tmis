"""Postgres-backed `VersioningPort` (T5 of the "cases -> drafting"
persistent & isolated slice, docs/28-legal-drafting.md). Every draft
snapshot is core drafting state — unlike history/validation/review/
style, which stay in-memory this sprint (documented debt) — so it gets
its own table, `drafting_document_versions`, scoped by `firm_id` exactly
like `drafting_documents` (ADR-SLICE-01/02).

Same shape as `SQLAlchemyDraftDocumentStore`: built on the request's own
`Session` plus the caller's `firm_id`, fixed for the instance's whole
lifetime, so `VersioningPort`'s methods keep their original signatures
(no `firm_id` parameter to thread through) while every query still goes
through `core.tenancy.scoped_query`.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.types import JSON

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.tenancy import scoped_query
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.versioning.diffing import diff_versions
from tmis.legal_drafting.versioning.schemas import DocumentVersion, VersionDiff


class DraftDocumentVersionModel(Base):
    """One row per snapshot. `document_id` + `version_number` are unique
    together; `firm_id` is indexed for `scoped_query` and never part of
    `payload` (tenancy metadata never lives inside the domain blob, same
    rule as `DraftDocumentModel`)."""

    __tablename__ = "drafting_document_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[list[Any]] = mapped_column(JSON, nullable=False)


def _row_to_version(row: DraftDocumentVersionModel) -> DocumentVersion:
    sections: tuple[Section, ...] = from_json(row.payload, tuple[Section, ...])
    return DocumentVersion(
        id=row.id,
        document_id=row.document_id,
        version_number=row.version_number,
        sections=sections,
        author=row.author,
        created_at=row.created_at,
    )


class SQLAlchemyVersioningService:
    """Implements `VersioningPort`. Built fresh per request by
    `tmis.legal_drafting.bootstrap.get_document_orchestrator` — never
    cached, never shared between tenants (ADR-SLICE-02)."""

    def __init__(self, session: Session, firm_id: uuid.UUID) -> None:
        self._session = session
        self._firm_id = str(firm_id)

    def snapshot(self, document_id: str, sections: list[Section], author: str) -> DocumentVersion:
        version_number = len(self.list_versions(document_id)) + 1
        version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=version_number,
            sections=tuple(sections),
            author=author,
            created_at=datetime.now(UTC),
        )
        row = DraftDocumentVersionModel(
            id=version.id,
            document_id=document_id,
            firm_id=self._firm_id,
            version_number=version_number,
            author=author,
            created_at=version.created_at,
            payload=to_json(version.sections),
        )
        self._session.add(row)
        self._session.commit()
        return version

    def list_versions(self, document_id: str) -> list[DocumentVersion]:
        stmt = (
            scoped_query(DraftDocumentVersionModel, self._firm_id)
            .where(DraftDocumentVersionModel.document_id == document_id)
            .order_by(DraftDocumentVersionModel.version_number)
        )
        return [_row_to_version(row) for row in self._session.scalars(stmt)]

    def get(self, document_id: str, version_number: int) -> DocumentVersion | None:
        stmt = scoped_query(DraftDocumentVersionModel, self._firm_id).where(
            DraftDocumentVersionModel.document_id == document_id,
            DraftDocumentVersionModel.version_number == version_number,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return _row_to_version(row) if row is not None else None

    def compare(self, document_id: str, version_a: int, version_b: int) -> VersionDiff:
        va = self.get(document_id, version_a)
        vb = self.get(document_id, version_b)
        if va is None or vb is None:
            raise ValueError(f"Unknown version for document {document_id!r}")
        return diff_versions(va, vb)

    def restore(self, document_id: str, version_number: int) -> list[Section]:
        version = self.get(document_id, version_number)
        if version is None:
            raise ValueError(f"Unknown version {version_number} for document {document_id!r}")
        return list(version.sections)


__all__ = ["DraftDocumentVersionModel", "SQLAlchemyVersioningService"]
