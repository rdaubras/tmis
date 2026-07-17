"""SQLAlchemy-backed implementation of `ResearchHistoryPort` (ADR-RESEARCH-02,
"legal_research" persistent & isolated slice, see docs/21-legal-research.md).

Persists `ResearchHistoryEntry` rows in Postgres. This port is an
append-only audit log (`record`, not `save`) — every call to `record`
inserts a new row, never overwriting a prior entry, mirroring
`InMemoryResearchHistory`'s `list.append` semantics.

The dataclass's own `id` field is *not* used as the primary key: the
Protocol gives no uniqueness guarantee for it, so a surrogate UUID
`row_id` is the primary key instead, with `entry_id` (the business
`id`) kept as an indexed, non-unique column.

Same shape as `SQLAlchemyDraftDocumentStore`/`SQLAlchemyVersioningService`
(the `cases -> drafting` slice's pattern, docs/28-legal-drafting.md
ADR-SLICE-02): built on the request's own `Session` plus the caller's
`firm_id`, fixed for the instance's whole lifetime, so `firm_id` is never
a method parameter and every query still goes through
`core.tenancy.scoped_query` — a history entry belongs to exactly one
cabinet, never all of them (ADR-RESEARCH-02).

`list_for_user`/`list_for_case`/`list_all` order rows by `timestamp`
ascending (then `row_id` as a tiebreaker for deterministic ordering
when timestamps collide) to mirror the in-memory store's insertion
order — callers assign `timestamp` at record-time, so ascending
timestamp order matches append order in practice.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.tenancy import scoped_query
from tmis.legal_research.history.schemas import ResearchHistoryEntry

_PULLED_FIELDS = ("id", "user_id", "case_id", "timestamp")


class ResearchHistoryEntryModel(Base):
    __tablename__ = "research_history_entries"

    row_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    case_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SQLAlchemyResearchHistory:
    """Implements `ResearchHistoryPort` against a real database, scoped to
    exactly one firm for its whole lifetime. Built fresh per request by
    `tmis.legal_research.bootstrap.get_research_orchestrator` — never
    cached, never shared between tenants (ADR-RESEARCH-02)."""

    def __init__(self, session: Session, firm_id: uuid.UUID) -> None:
        self._session = session
        self._firm_id = str(firm_id)

    def record(self, entry: ResearchHistoryEntry) -> None:
        full = to_json(entry)
        payload = {k: v for k, v in full.items() if k not in _PULLED_FIELDS}
        row = ResearchHistoryEntryModel(
            entry_id=entry.id,
            firm_id=self._firm_id,
            user_id=entry.user_id,
            case_id=entry.case_id,
            timestamp=entry.timestamp,
            payload=payload,
        )
        self._session.add(row)
        self._session.commit()

    def list_for_user(self, user_id: str) -> list[ResearchHistoryEntry]:
        stmt = (
            scoped_query(ResearchHistoryEntryModel, self._firm_id)
            .where(ResearchHistoryEntryModel.user_id == user_id)
            .order_by(ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id)
        )
        return [self._to_entry(row) for row in self._session.scalars(stmt)]

    def list_for_case(self, case_id: str) -> list[ResearchHistoryEntry]:
        stmt = (
            scoped_query(ResearchHistoryEntryModel, self._firm_id)
            .where(ResearchHistoryEntryModel.case_id == case_id)
            .order_by(ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id)
        )
        return [self._to_entry(row) for row in self._session.scalars(stmt)]

    def list_all(self) -> list[ResearchHistoryEntry]:
        stmt = scoped_query(ResearchHistoryEntryModel, self._firm_id).order_by(
            ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id
        )
        return [self._to_entry(row) for row in self._session.scalars(stmt)]

    @staticmethod
    def _to_entry(row: ResearchHistoryEntryModel) -> ResearchHistoryEntry:
        combined: dict[str, Any] = dict(row.payload)
        combined["id"] = row.entry_id
        combined["user_id"] = row.user_id
        combined["case_id"] = row.case_id
        combined["timestamp"] = row.timestamp
        result: ResearchHistoryEntry = from_json(combined, ResearchHistoryEntry)
        return result


__all__ = ["ResearchHistoryEntryModel", "SQLAlchemyResearchHistory"]
