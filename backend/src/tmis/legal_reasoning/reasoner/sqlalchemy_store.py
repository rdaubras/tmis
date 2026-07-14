"""Postgres-backed `SessionStorePort` (Sprint 26 — Module Document +
Persistance, see docs/151-architecture-persistance.md). Sits behind the
exact same port as `InMemorySessionStore`
(`tmis.legal_reasoning.reasoner.ports.SessionStorePort`) —
`ReasoningOrchestrator` never knows which one it was given.

Reuses `tmis.core.db.base.Base` (the repo's single declarative base) and
`tmis.core.db.dataclass_json` (the shared dataclass<->JSON codec used by
every domain store this sprint) — no second persistence mechanism, no
per-domain (de)serialization code.

`save()` is a plain upsert-by-id, matching `InMemorySessionStore`'s
`self._sessions[session.id] = session` (an overwrite, never an append) —
unlike `document_intelligence`'s store this domain has no versioning
concept on its port.
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession

_EXCLUDED_FROM_PAYLOAD = ("id", "case_id", "created_at")


class ReasoningSessionModel(Base):
    """One row per `ReasoningSession`, keyed by its own `id` (already a
    UUID string minted by `ReasoningOrchestrator.reason()`) — no
    surrogate primary key needed."""

    __tablename__ = "reasoning_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


def _session_to_row_fields(session: ReasoningSession) -> dict[str, Any]:
    full = to_json(session)
    payload = {k: v for k, v in full.items() if k not in _EXCLUDED_FROM_PAYLOAD}
    return {"payload": payload}


def _row_to_session(row: ReasoningSessionModel) -> ReasoningSession:
    combined: dict[str, Any] = dict(row.payload)
    combined["id"] = row.id
    combined["case_id"] = row.case_id
    combined["created_at"] = row.created_at
    result: ReasoningSession = from_json(combined, ReasoningSession)
    return result


class SQLAlchemySessionStore:
    """Implements `SessionStorePort` exactly (same methods, same return
    types as `InMemorySessionStore`) on top of the repo's single sync
    SQLAlchemy engine — see `tmis.core.db.session` for why the sync
    engine is used here (the port's methods are synchronous, so the
    adapter must be too)."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def get(self, session_id: str) -> ReasoningSession | None:
        with self._session_factory() as session:
            row = session.execute(
                select(ReasoningSessionModel).where(ReasoningSessionModel.id == session_id)
            ).scalar_one_or_none()
            return _row_to_session(row) if row is not None else None

    def save(self, session: ReasoningSession) -> None:
        with self._session_factory() as db_session:
            row_fields = _session_to_row_fields(session)
            row = ReasoningSessionModel(
                id=session.id,
                case_id=session.case_id,
                created_at=session.created_at,
                **row_fields,
            )
            db_session.merge(row)
            db_session.commit()

    def list_ids(self) -> list[str]:
        with self._session_factory() as db_session:
            rows = db_session.execute(select(ReasoningSessionModel.id)).all()
            return [row[0] for row in rows]


__all__ = ["ReasoningSessionModel", "SQLAlchemySessionStore"]
