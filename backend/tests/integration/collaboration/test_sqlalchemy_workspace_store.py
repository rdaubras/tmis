"""Integration test for `SQLAlchemyWorkspaceStore` against a real (sqlite)
database — exercises the actual SQL round-trip, not a mock."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.collaboration.workspace.adapters.sqlalchemy_store import SQLAlchemyWorkspaceStore
from tmis.collaboration.workspace.ports import WorkspaceStorePort
from tmis.collaboration.workspace.schemas import Workspace, WorkspaceSettings
from tmis.core.db.base import Base


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["workspaces"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["workspaces"]])


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemyWorkspaceStore:
    return SQLAlchemyWorkspaceStore(session_factory=session_factory)


def _sample_workspace(
    workspace_id: str,
    firm_id: str,
    *,
    name: str = "Workspace principal",
) -> Workspace:
    return Workspace(
        id=workspace_id,
        firm_id=firm_id,
        name=name,
        settings=WorkspaceSettings(default_role="lawyer", allow_client_comments=True),
        member_ids={"user-1", "user-2"},
        case_ids={"case-1", "case-2"},
        team_ids={"team-1"},
        document_ids={"doc-1", "doc-2", "doc-3"},
        task_ids={"task-1"},
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


def test_store_implements_workspace_store_port(store: SQLAlchemyWorkspaceStore) -> None:
    port: WorkspaceStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemyWorkspaceStore) -> None:
    workspace = _sample_workspace("ws-1", "firm-1")

    store.save(workspace)
    fetched = store.get("ws-1")

    assert fetched is not None
    assert fetched == workspace
    assert fetched.settings == workspace.settings
    assert fetched.member_ids == workspace.member_ids
    assert fetched.case_ids == workspace.case_ids
    assert fetched.team_ids == workspace.team_ids
    assert fetched.document_ids == workspace.document_ids
    assert fetched.task_ids == workspace.task_ids
    assert fetched.created_at == workspace.created_at


def test_get_missing_workspace_returns_none(store: SQLAlchemyWorkspaceStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_for_firm_returns_only_that_firms_workspaces(
    store: SQLAlchemyWorkspaceStore,
) -> None:
    ws_a1 = _sample_workspace("ws-a1", "firm-a", name="A1")
    ws_a2 = _sample_workspace("ws-a2", "firm-a", name="A2")
    ws_b1 = _sample_workspace("ws-b1", "firm-b", name="B1")

    store.save(ws_a1)
    store.save(ws_a2)
    store.save(ws_b1)

    firm_a_workspaces = store.list_for_firm("firm-a")

    assert {w.id for w in firm_a_workspaces} == {"ws-a1", "ws-a2"}
    assert all(w.firm_id == "firm-a" for w in firm_a_workspaces)


def test_list_ids_returns_distinct_workspace_ids(store: SQLAlchemyWorkspaceStore) -> None:
    store.save(_sample_workspace("ws-1", "firm-1"))
    store.save(_sample_workspace("ws-2", "firm-1"))

    assert sorted(store.list_ids()) == ["ws-1", "ws-2"]


def test_resaving_existing_workspace_id_overwrites_rather_than_duplicates(
    store: SQLAlchemyWorkspaceStore,
) -> None:
    store.save(_sample_workspace("ws-1", "firm-1", name="Original Name"))
    store.save(_sample_workspace("ws-1", "firm-1", name="Updated Name"))

    fetched = store.get("ws-1")
    assert fetched is not None
    assert fetched.name == "Updated Name"
    assert store.list_ids() == ["ws-1"]
