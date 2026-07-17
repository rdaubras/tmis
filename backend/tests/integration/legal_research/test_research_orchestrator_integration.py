import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401 — registers research_history_entries
import tmis.legal_research.search.sqlalchemy_store  # noqa: F401 — registers research_searches
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.legal_research.bootstrap import clear_research_caches, get_research_orchestrator

_FIRM_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path: object) -> Iterator[Session]:
    """`get_kernel`/the stateless `legal_research.bootstrap` singletons
    are `lru_cache`d process-wide; reset them before each test so
    connector registrations from one test don't leak into another.
    `get_research_orchestrator` is no longer one of those singletons
    (ADR-RESEARCH-02, see docs/21-legal-research.md): it is assembled per
    request on a `Session` and a `firm_id`, so tests now call it
    directly with both, the same way a route would receive them from
    `Depends`."""
    sync_engine = create_engine(
        f"sqlite:///{tmp_path}/research-orchestrator.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_base.Base.metadata.create_all(sync_engine)
    core_db_session.SessionLocal.configure(bind=sync_engine)

    clear_research_caches()
    get_kernel.cache_clear()

    session_factory: sessionmaker[Session] = sessionmaker(bind=sync_engine)
    with session_factory() as session:
        yield session


def _orchestrator(session: Session):  # noqa: ANN201
    return get_research_orchestrator(session=session, firm_id=_FIRM_ID)


@pytest.mark.asyncio
async def test_bootstrap_registers_lre_connectors_on_the_shared_kernel(
    _clear_singletons: Session,
) -> None:
    _orchestrator(_clear_singletons)
    kernel = get_kernel()
    assert "internal_documentation" in kernel.connector_manager.list_connectors()
    assert "private_database" in kernel.connector_manager.list_connectors()
    # Sprint 2 connectors are still there — the LRE extends, not replaces.
    assert "codes" in kernel.connector_manager.list_connectors()


@pytest.mark.asyncio
async def test_search_reaches_a_sprint_2_connector_end_to_end(_clear_singletons: Session) -> None:
    orchestrator = _orchestrator(_clear_singletons)
    response = await orchestrator.search("contrat de travail", connector_names=["codes"])
    assert response.results
    assert all(r.connector == "codes" for r in response.results)


@pytest.mark.asyncio
async def test_search_reaches_the_lre_own_connectors_end_to_end(
    _clear_singletons: Session,
) -> None:
    orchestrator = _orchestrator(_clear_singletons)
    response = await orchestrator.search(
        "non-concurrence", connector_names=["internal_documentation", "private_database"]
    )
    assert response.results
    connectors = {r.connector for r in response.results}
    assert connectors <= {"internal_documentation", "private_database"}


@pytest.mark.asyncio
async def test_search_degrades_gracefully_when_a_connector_is_disabled(
    _clear_singletons: Session,
) -> None:
    kernel = get_kernel()
    orchestrator = _orchestrator(_clear_singletons)
    kernel.connector_manager.disable("internal_documentation")

    response = await orchestrator.search(
        "non-concurrence", connector_names=["internal_documentation", "private_database"]
    )

    assert all(r.connector != "internal_documentation" for r in response.results)


@pytest.mark.asyncio
async def test_search_response_is_retrievable_after_the_fact(_clear_singletons: Session) -> None:
    orchestrator = _orchestrator(_clear_singletons)
    response = await orchestrator.search("contrat de travail", connector_names=["codes"])

    retrieved = orchestrator.get_response(response.search_id)
    citations = orchestrator.get_citations(response.search_id)

    assert retrieved == response
    assert citations is not None
    assert len(citations) == len(response.results)
