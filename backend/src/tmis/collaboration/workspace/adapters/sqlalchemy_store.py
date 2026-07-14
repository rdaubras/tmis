"""Postgres-backed `WorkspaceStorePort` (Sprint 26 — see
docs/151-architecture-persistance.md). Sits behind the exact same port as
`InMemoryWorkspaceStore` (`tmis.collaboration.workspace.store.
InMemoryWorkspaceStore`) — callers never know which one they were given.

Reuses `tmis.core.db.base.Base` (the repo's single declarative base) and
`tmis.core.db.dataclass_json` (the shared dataclass<->JSON codec used by
every domain store this sprint) — no second persistence mechanism, no
per-domain (de)serialization code.

One row per workspace, upserted on `save()` to match
`InMemoryWorkspaceStore`'s overwrite semantics (`self._workspaces[workspace.
id] = workspace`).
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.collaboration.workspace.schemas import Workspace
from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal


class WorkspaceModel(Base):
    """One row per workspace. `id` and `firm_id` get dedicated columns
    (the latter indexed for `list_for_firm`); everything else is stored
    as one JSON payload."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


_EXCLUDED_FROM_PAYLOAD = ("id", "firm_id")


def _workspace_to_payload(workspace: Workspace) -> dict[str, Any]:
    full = to_json(workspace)
    return {k: v for k, v in full.items() if k not in _EXCLUDED_FROM_PAYLOAD}


def _row_to_workspace(row: WorkspaceModel) -> Workspace:
    combined: dict[str, Any] = dict(row.payload)
    combined["id"] = row.id
    combined["firm_id"] = row.firm_id
    result: Workspace = from_json(combined, Workspace)
    return result


class SQLAlchemyWorkspaceStore:
    """Implements `WorkspaceStorePort` exactly (same methods, same return
    types as `InMemoryWorkspaceStore`) on top of the repo's single sync
    SQLAlchemy engine — the port's methods are synchronous, so the adapter
    must be too."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def get(self, workspace_id: str) -> Workspace | None:
        with self._session_factory() as session:
            row = session.execute(
                select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
            ).scalar_one_or_none()
            return _row_to_workspace(row) if row is not None else None

    def save(self, workspace: Workspace) -> None:
        with self._session_factory() as session:
            row = WorkspaceModel(
                id=workspace.id,
                firm_id=workspace.firm_id,
                payload=_workspace_to_payload(workspace),
            )
            session.merge(row)
            session.commit()

    def list_for_firm(self, firm_id: str) -> list[Workspace]:
        with self._session_factory() as session:
            rows = (
                session.execute(select(WorkspaceModel).where(WorkspaceModel.firm_id == firm_id))
                .scalars()
                .all()
            )
            return [_row_to_workspace(row) for row in rows]

    def list_ids(self) -> list[str]:
        with self._session_factory() as session:
            rows = session.execute(select(WorkspaceModel.id)).scalars().all()
            return list(rows)


__all__ = ["WorkspaceModel", "SQLAlchemyWorkspaceStore"]
