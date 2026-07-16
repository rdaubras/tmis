from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow, get_case_store
from tmis.case_intelligence.facts.schemas import Fact
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path: object) -> Iterator[None]:
    """All bootstrap accessors are `lru_cache`d process-wide singletons;
    reset them before each test so state from one test never leaks into
    another (see docs/25-legal-reasoning.md).

    `workflow.case_store` is a `SQLAlchemyCaseStore` since Sprint 43 (see
    docs/151-architecture-persistance.md), so point it at a throwaway
    sqlite database — same real-DB fixture pattern as `test_case_api.py`
    — instead of letting it fall through to whatever `SessionLocal` bind
    a previous test file left behind."""
    sync_engine = create_engine(
        f"sqlite:///{tmp_path}/sprint43-reasoning-orchestrator.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_base.Base.metadata.create_all(
        sync_engine, tables=[core_db_base.Base.metadata.tables["case_profiles"]]
    )
    core_db_session.SessionLocal.configure(bind=sync_engine)

    get_reasoning_orchestrator.cache_clear()
    get_research_orchestrator.cache_clear()
    get_case_intelligence_workflow.cache_clear()
    get_case_store.cache_clear()
    get_kernel.cache_clear()

    yield


@pytest.mark.asyncio
async def test_reason_reaches_a_real_sprint2_connector_end_to_end() -> None:
    orchestrator = get_reasoning_orchestrator()

    # The Sprint 2 mock connectors do a naive substring match (see
    # docs/21-legal-research.md), so the question must literally contain a
    # substring of the `codes` fixture ("Le contrat de travail à durée
    # indéterminée peut être rompu...") for a real result to come back.
    session = await orchestrator.reason("contrat de travail à durée indéterminée peut être rompu")

    assert session.hypotheses
    assert any(a.source_connector == "codes" for a in session.arguments)


@pytest.mark.asyncio
async def test_reason_consumes_case_facts_from_the_shared_case_intelligence_workflow() -> None:
    workflow = get_case_intelligence_workflow()
    profile = workflow.case_store.get_or_create("case-1", title="Dossier test")
    profile.facts.append(
        Fact(
            id="fact-1",
            description="Le contrat de travail a été rompu le 3 mars.",
            confidence=0.8,
            source_document_ids={"doc-1"},
            contradicting_document_ids={"doc-2"},
        )
    )
    workflow.case_store.save(profile)

    orchestrator = get_reasoning_orchestrator()
    session = await orchestrator.reason(
        "contrat de travail à durée indéterminée peut être rompu", case_id="case-1"
    )

    assert session.case_id == "case-1"
    assert any("fact-1" in h.supporting_fact_ids for h in session.hypotheses)
    assert session.conflicts


@pytest.mark.asyncio
async def test_reason_produces_a_non_empty_synthesis_via_the_shared_kernel() -> None:
    orchestrator = get_reasoning_orchestrator()
    session = await orchestrator.reason("contrat de travail à durée indéterminée peut être rompu")
    assert session.synthesis


@pytest.mark.asyncio
async def test_reasoning_orchestrator_shares_the_kernel_event_bus() -> None:
    kernel = get_kernel()
    orchestrator = get_reasoning_orchestrator()
    assert orchestrator.event_bus is kernel.event_bus
