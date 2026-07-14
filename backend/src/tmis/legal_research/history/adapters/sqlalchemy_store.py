"""SQLAlchemy-backed implementation of `ResearchHistoryPort`.

Persists `ResearchHistoryEntry` rows in Postgres. This port is an
append-only audit log (`record`, not `save`) — every call to `record`
inserts a new row, never overwriting a prior entry, mirroring
`InMemoryResearchHistory`'s `list.append` semantics.

The dataclass's own `id` field is *not* used as the primary key: the
Protocol gives no uniqueness guarantee for it, so a surrogate UUID
`row_id` is the primary key instead, with `entry_id` (the business
`id`) kept as an indexed, non-unique column.

`list_for_user`/`list_for_case`/`list_all` order rows by `timestamp`
ascending (then `row_id` as a tiebreaker for deterministic ordering
when timestamps collide) to mirror the in-memory store's insertion
order — callers assign `timestamp` at record-time, so ascending
timestamp order matches append order in practice.
"""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal
from tmis.legal_research.history.schemas import ResearchHistoryEntry

_PULLED_FIELDS = ("id", "user_id", "case_id", "timestamp")


class ResearchHistoryEntryModel(Base):
    __tablename__ = "research_history_entries"

    row_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    case_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SQLAlchemyResearchHistory:
    """Implements `ResearchHistoryPort` against a real database."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def record(self, entry: ResearchHistoryEntry) -> None:
        with self._session_factory() as session:
            full = to_json(entry)
            payload = {k: v for k, v in full.items() if k not in _PULLED_FIELDS}
            row = ResearchHistoryEntryModel(
                entry_id=entry.id,
                user_id=entry.user_id,
                case_id=entry.case_id,
                timestamp=entry.timestamp,
                payload=payload,
            )
            session.add(row)
            session.commit()

    def list_for_user(self, user_id: str) -> list[ResearchHistoryEntry]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ResearchHistoryEntryModel)
                .where(ResearchHistoryEntryModel.user_id == user_id)
                .order_by(ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id)
            ).scalars()
            return [self._to_entry(row) for row in rows]

    def list_for_case(self, case_id: str) -> list[ResearchHistoryEntry]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ResearchHistoryEntryModel)
                .where(ResearchHistoryEntryModel.case_id == case_id)
                .order_by(ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id)
            ).scalars()
            return [self._to_entry(row) for row in rows]

    def list_all(self) -> list[ResearchHistoryEntry]:
        with self._session_factory() as session:
            rows = session.execute(
                select(ResearchHistoryEntryModel).order_by(
                    ResearchHistoryEntryModel.timestamp, ResearchHistoryEntryModel.row_id
                )
            ).scalars()
            return [self._to_entry(row) for row in rows]

    @staticmethod
    def _to_entry(row: ResearchHistoryEntryModel) -> ResearchHistoryEntry:
        combined: dict[str, Any] = dict(row.payload)
        combined["id"] = row.entry_id
        combined["user_id"] = row.user_id
        combined["case_id"] = row.case_id
        combined["timestamp"] = row.timestamp
        result: ResearchHistoryEntry = from_json(combined, ResearchHistoryEntry)
        return result
