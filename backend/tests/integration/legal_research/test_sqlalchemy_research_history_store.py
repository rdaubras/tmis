"""Integration test for `SQLAlchemyResearchHistory` against a real
(sqlite) database — exercises the actual SQL round-trip, not a mock."""

from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.core.db.base import Base
from tmis.legal_research.history.adapters.sqlalchemy_store import SQLAlchemyResearchHistory
from tmis.legal_research.history.ports import ResearchHistoryPort
from tmis.legal_research.history.schemas import ResearchHistoryEntry


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(
        engine, tables=[Base.metadata.tables["research_history_entries"]]
    )
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["research_history_entries"]])


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemyResearchHistory:
    return SQLAlchemyResearchHistory(session_factory=session_factory)


# Naive datetime: SQLite's DateTime column drops tzinfo on round-trip
# (a driver quirk of this test's in-memory fixture, not of Postgres),
# so the fixture uses naive datetimes to keep the round-trip assertion
# exact regardless of backend.
_BASE_TIME = datetime(2026, 7, 14, 12, 0, 0)


def _entry(
    entry_id: str,
    *,
    offset_seconds: int = 0,
    user_id: str | None = None,
    case_id: str | None = None,
) -> ResearchHistoryEntry:
    return ResearchHistoryEntry(
        id=entry_id,
        query_text=f"query for {entry_id}",
        timestamp=_BASE_TIME + timedelta(seconds=offset_seconds),
        connectors_used=("legifrance", "dalloz"),
        duration_ms=123.45,
        result_count=7,
        user_id=user_id,
        case_id=case_id,
    )


def test_store_implements_research_history_port(store: SQLAlchemyResearchHistory) -> None:
    port: ResearchHistoryPort = store
    assert port is not None


def test_record_then_list_all_round_trips_every_field(
    store: SQLAlchemyResearchHistory,
) -> None:
    entry = _entry("run-1", user_id="user-1", case_id="case-1")

    store.record(entry)
    entries = store.list_all()

    assert len(entries) == 1
    fetched = entries[0]
    assert fetched.id == entry.id
    assert fetched.query_text == entry.query_text
    assert fetched.timestamp == entry.timestamp
    assert fetched.connectors_used == entry.connectors_used
    assert fetched.duration_ms == entry.duration_ms
    assert fetched.result_count == entry.result_count
    assert fetched.user_id == entry.user_id
    assert fetched.case_id == entry.case_id


def test_record_with_neither_user_nor_case(store: SQLAlchemyResearchHistory) -> None:
    entry = _entry("run-anon", offset_seconds=1)

    store.record(entry)
    entries = store.list_all()

    assert len(entries) == 1
    assert entries[0].user_id is None
    assert entries[0].case_id is None


def test_list_for_user_filters_correctly(store: SQLAlchemyResearchHistory) -> None:
    store.record(_entry("run-1", offset_seconds=0, user_id="user-1"))
    store.record(_entry("run-2", offset_seconds=1, user_id="user-2"))
    store.record(_entry("run-3", offset_seconds=2, user_id="user-1", case_id="case-1"))
    store.record(_entry("run-4", offset_seconds=3))

    results = store.list_for_user("user-1")

    assert [e.id for e in results] == ["run-1", "run-3"]


def test_list_for_case_filters_correctly(store: SQLAlchemyResearchHistory) -> None:
    store.record(_entry("run-1", offset_seconds=0, case_id="case-1"))
    store.record(_entry("run-2", offset_seconds=1, case_id="case-2"))
    store.record(_entry("run-3", offset_seconds=2, user_id="user-1", case_id="case-1"))
    store.record(_entry("run-4", offset_seconds=3))

    results = store.list_for_case("case-1")

    assert [e.id for e in results] == ["run-1", "run-3"]


def test_ordering_is_stable_and_matches_insertion_order(
    store: SQLAlchemyResearchHistory,
) -> None:
    store.record(_entry("run-1", offset_seconds=0, user_id="user-1"))
    store.record(_entry("run-2", offset_seconds=5, user_id="user-1"))
    store.record(_entry("run-3", offset_seconds=10, user_id="user-1"))

    assert [e.id for e in store.list_all()] == ["run-1", "run-2", "run-3"]
    assert [e.id for e in store.list_for_user("user-1")] == ["run-1", "run-2", "run-3"]


def test_record_never_overwrites_prior_entries(store: SQLAlchemyResearchHistory) -> None:
    store.record(_entry("dup-id", offset_seconds=0, user_id="user-1"))
    store.record(_entry("dup-id", offset_seconds=1, user_id="user-1"))

    entries = store.list_all()

    assert len(entries) == 2
    assert [e.id for e in entries] == ["dup-id", "dup-id"]


def test_list_for_user_returns_empty_for_unknown_user(
    store: SQLAlchemyResearchHistory,
) -> None:
    store.record(_entry("run-1", user_id="user-1"))

    assert store.list_for_user("no-such-user") == []


def test_list_for_case_returns_empty_for_unknown_case(
    store: SQLAlchemyResearchHistory,
) -> None:
    store.record(_entry("run-1", case_id="case-1"))

    assert store.list_for_case("no-such-case") == []
