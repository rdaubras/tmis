"""Integration test for `SQLAlchemyResearchSearchStore` against a real
(sqlite) database — exercises the actual SQL round-trip, not a mock."""

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.core.db.base import Base
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.ports import ResearchSearchStorePort
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult
from tmis.legal_research.search.sqlalchemy_store import SQLAlchemyResearchSearchStore

_FIRM_ID = uuid.uuid4()
_OTHER_FIRM_ID = uuid.uuid4()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["research_searches"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["research_searches"]])


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def store(session: Session) -> SQLAlchemyResearchSearchStore:
    return SQLAlchemyResearchSearchStore(session, _FIRM_ID)


def _result(result_id: str = "r1") -> ResearchResult:
    return ResearchResult(
        id=result_id,
        title="Cass. soc., 9 juin 2021",
        excerpt="Extrait pertinent",
        connector="private_database",
        document_type="jurisprudence",
        reference="19-24.354",
        date="2021-06-09",
        lexical_score=0.8,
        vector_score=0.7,
        authority_score=0.6,
        freshness_score=0.5,
        final_score=0.9,
    )


def _response(search_id: str = "search-1") -> ResearchResponse:
    return ResearchResponse(
        search_id=search_id,
        query="non-concurrence",
        results=(_result(),),
        connectors_used=("private_database",),
        duration_ms=42.0,
        cache_hit=False,
    )


def _citations() -> tuple[ResearchCitation, ...]:
    return (
        ResearchCitation(
            source_id="r1",
            title="Cass. soc., 9 juin 2021",
            date="2021-06-09",
            document_type="jurisprudence",
            reference="19-24.354",
            excerpt="Extrait pertinent",
        ),
    )


def test_store_implements_research_search_store_port(
    store: SQLAlchemyResearchSearchStore,
) -> None:
    port: ResearchSearchStorePort = store
    assert port is not None


def test_save_then_get_round_trips_the_response(store: SQLAlchemyResearchSearchStore) -> None:
    response = _response("search-1")

    store.save(response, _citations(), user_id="user-1", case_id="case-1")
    fetched = store.get("search-1")

    assert fetched == response


def test_save_then_get_citations_round_trips(store: SQLAlchemyResearchSearchStore) -> None:
    citations = _citations()
    store.save(_response("search-1"), citations, user_id="user-1")

    fetched = store.get_citations("search-1")

    assert fetched == citations


def test_get_missing_search_returns_none(store: SQLAlchemyResearchSearchStore) -> None:
    assert store.get("does-not-exist") is None
    assert store.get_citations("does-not-exist") is None


def test_a_search_saved_by_one_firm_is_invisible_to_another(session: Session) -> None:
    store_a = SQLAlchemyResearchSearchStore(session, _FIRM_ID)
    store_b = SQLAlchemyResearchSearchStore(session, _OTHER_FIRM_ID)

    store_a.save(_response("search-1"), _citations(), user_id="user-1")

    assert store_b.get("search-1") is None
    assert store_b.get_citations("search-1") is None
    assert store_a.get("search-1") is not None
