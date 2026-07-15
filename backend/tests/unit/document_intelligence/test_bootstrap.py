import pytest

from tmis.agents.bootstrap import get_contract_agent
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.document_intelligence.bootstrap import get_document_pipeline, get_document_store


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Every composition root touched by this module is an `lru_cache`d
    process-wide singleton; reset them before each test so identity
    assertions never depend on what a previous test constructed first."""
    get_document_store.cache_clear()
    get_document_pipeline.cache_clear()
    get_contract_agent.cache_clear()
    get_kernel.cache_clear()


def test_get_document_store_is_a_process_wide_singleton() -> None:
    assert get_document_store() is get_document_store()


def test_get_document_pipeline_shares_the_document_store_singleton() -> None:
    pipeline = get_document_pipeline()

    assert pipeline.document_store is get_document_store()


def test_get_contract_agent_shares_the_document_store_singleton() -> None:
    agent = get_contract_agent()

    assert agent._document_store is get_document_store()  # noqa: SLF001


def test_orchestrator_analysis_agent_shares_the_document_store_singleton() -> None:
    orchestrator = Orchestrator()

    assert orchestrator._analysis_agent._document_store is get_document_store()  # noqa: SLF001
