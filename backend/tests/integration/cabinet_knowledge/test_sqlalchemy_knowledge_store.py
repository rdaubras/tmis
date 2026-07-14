"""Integration test for `SQLAlchemyKnowledgeStore` against a real (sqlite)
database — exercises the actual SQL round-trip, not a mock."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.cabinet_knowledge.knowledge.adapters.sqlalchemy_store import SQLAlchemyKnowledgeStore
from tmis.cabinet_knowledge.knowledge.ports import KnowledgeStorePort
from tmis.cabinet_knowledge.knowledge.schemas import (
    KnowledgeObject,
    KnowledgeStatus,
    KnowledgeType,
)
from tmis.core.db.base import Base


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["knowledge_objects"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["knowledge_objects"]])


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemyKnowledgeStore:
    return SQLAlchemyKnowledgeStore(session_factory=session_factory)


def _sample_object(
    object_id: str,
    *,
    firm_id: str = "firm-1",
    type_: KnowledgeType = KnowledgeType.PLAYBOOK,
    title: str = "Negotiation playbook",
) -> KnowledgeObject:
    return KnowledgeObject(
        id=object_id,
        firm_id=firm_id,
        type=type_,
        title=title,
        content={"steps": ["identify", "negotiate", "close"], "difficulty": 3, "meta": {"a": 1}},
        author="jane.doe",
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC),
        version=2,
        status=KnowledgeStatus.VALIDATED,
        quality_score=0.87,
        tags=frozenset({"contract", "negotiation"}),
        relations=("know-related-1", "know-related-2"),
        is_published=True,
        usage_count=5,
    )


def test_store_implements_knowledge_store_port(store: SQLAlchemyKnowledgeStore) -> None:
    port: KnowledgeStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemyKnowledgeStore) -> None:
    obj = _sample_object("know-1")

    store.save(obj)
    fetched = store.get("know-1")

    assert fetched is not None
    assert fetched == obj
    assert fetched.content == obj.content
    assert fetched.tags == obj.tags
    assert fetched.relations == obj.relations


def test_get_missing_object_returns_none(store: SQLAlchemyKnowledgeStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_for_firm_returns_only_that_firms_objects(store: SQLAlchemyKnowledgeStore) -> None:
    obj_playbook = _sample_object("know-1", firm_id="firm-1", type_=KnowledgeType.PLAYBOOK)
    obj_clause = _sample_object("know-2", firm_id="firm-1", type_=KnowledgeType.CLAUSE)
    other_firm_obj = _sample_object("know-3", firm_id="firm-2", type_=KnowledgeType.PLAYBOOK)

    store.save(obj_playbook)
    store.save(obj_clause)
    store.save(other_firm_obj)

    results = store.list_for_firm("firm-1")

    assert {o.id for o in results} == {"know-1", "know-2"}
    assert "know-3" not in {o.id for o in results}


def test_list_for_firm_filters_by_type(store: SQLAlchemyKnowledgeStore) -> None:
    obj_playbook = _sample_object("know-1", firm_id="firm-1", type_=KnowledgeType.PLAYBOOK)
    obj_clause = _sample_object("know-2", firm_id="firm-1", type_=KnowledgeType.CLAUSE)
    store.save(obj_playbook)
    store.save(obj_clause)

    results = store.list_for_firm("firm-1", type_=KnowledgeType.CLAUSE)

    assert [o.id for o in results] == ["know-2"]


def test_resaving_existing_object_id_overwrites_rather_than_duplicates(
    store: SQLAlchemyKnowledgeStore,
) -> None:
    store.save(_sample_object("know-1", title="Original title"))
    store.save(_sample_object("know-1", title="Updated title"))

    fetched = store.get("know-1")
    assert fetched is not None
    assert fetched.title == "Updated title"
    assert len(store.list_for_firm("firm-1")) == 1
