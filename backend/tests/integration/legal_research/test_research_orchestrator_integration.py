import pytest

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import get_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """`get_research_orchestrator`/`get_kernel` are `lru_cache`d process-wide
    singletons; reset them before each test so connector registrations and
    history from one test don't leak into another."""
    get_research_orchestrator.cache_clear()
    get_kernel.cache_clear()


@pytest.mark.asyncio
async def test_bootstrap_registers_lre_connectors_on_the_shared_kernel() -> None:
    get_research_orchestrator()
    kernel = get_kernel()
    assert "internal_documentation" in kernel.connector_manager.list_connectors()
    assert "private_database" in kernel.connector_manager.list_connectors()
    # Sprint 2 connectors are still there — the LRE extends, not replaces.
    assert "codes" in kernel.connector_manager.list_connectors()


@pytest.mark.asyncio
async def test_search_reaches_a_sprint_2_connector_end_to_end() -> None:
    orchestrator = get_research_orchestrator()
    response = await orchestrator.search("contrat de travail", connector_names=["codes"])
    assert response.results
    assert all(r.connector == "codes" for r in response.results)


@pytest.mark.asyncio
async def test_search_reaches_the_lre_own_connectors_end_to_end() -> None:
    orchestrator = get_research_orchestrator()
    response = await orchestrator.search(
        "non-concurrence", connector_names=["internal_documentation", "private_database"]
    )
    assert response.results
    connectors = {r.connector for r in response.results}
    assert connectors <= {"internal_documentation", "private_database"}


@pytest.mark.asyncio
async def test_search_degrades_gracefully_when_a_connector_is_disabled() -> None:
    kernel = get_kernel()
    orchestrator = get_research_orchestrator()
    get_research_orchestrator()  # ensure connectors are registered
    kernel.connector_manager.disable("internal_documentation")

    response = await orchestrator.search(
        "non-concurrence", connector_names=["internal_documentation", "private_database"]
    )

    assert all(r.connector != "internal_documentation" for r in response.results)


@pytest.mark.asyncio
async def test_search_response_is_retrievable_after_the_fact() -> None:
    orchestrator = get_research_orchestrator()
    response = await orchestrator.search("contrat de travail", connector_names=["codes"])

    retrieved = orchestrator.get_response(response.search_id)
    citations = orchestrator.get_citations(response.search_id)

    assert retrieved == response
    assert citations is not None
    assert len(citations) == len(response.results)
