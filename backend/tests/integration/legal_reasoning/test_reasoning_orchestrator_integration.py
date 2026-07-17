import pytest

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import (
    clear_case_intelligence_caches,
    get_shared_case_intelligence_workflow,
)
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import clear_research_caches


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """All bootstrap accessors are `lru_cache`d process-wide singletons;
    reset them before each test so state from one test never leaks into
    another (see docs/25-legal-reasoning.md).

    `legal_reasoning` composes `get_shared_case_intelligence_workflow()`
    (ADR-CASEINT-01, docs/19-case-intelligence.md) — the legacy,
    non-firm-scoped, in-memory `CaseStorePort` — not the firm-scoped,
    persistent `SQLAlchemyCaseStore` `/api/v1/cases/*` uses, so no
    database setup is needed here."""
    get_reasoning_orchestrator.cache_clear()
    clear_research_caches()
    clear_case_intelligence_caches()
    get_kernel.cache_clear()


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
    workflow = get_shared_case_intelligence_workflow()
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
