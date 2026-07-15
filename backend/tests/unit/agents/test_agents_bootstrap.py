import pytest

from tmis.agents.bootstrap import get_orchestrator
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.document_intelligence.bootstrap import get_document_store


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Every composition root touched by this module is an `lru_cache`d
    process-wide singleton; reset them before each test so identity
    assertions never depend on what a previous test constructed first —
    same pattern as `tests/unit/document_intelligence/test_bootstrap.py`
    (Sprint 37)."""
    get_orchestrator.cache_clear()
    get_kernel.cache_clear()
    get_ai_intelligence_fabric.cache_clear()
    get_ai_governance_platform.cache_clear()
    get_case_intelligence_workflow.cache_clear()
    get_document_store.cache_clear()


def test_get_orchestrator_is_a_process_wide_singleton() -> None:
    assert get_orchestrator() is get_orchestrator()


def test_get_orchestrator_agents_share_the_kernel_singleton() -> None:
    orchestrator = get_orchestrator()
    kernel = get_kernel()

    assert orchestrator._analysis_agent._kernel is kernel  # noqa: SLF001
    assert orchestrator._synthesis_agent._kernel is kernel  # noqa: SLF001


def test_get_orchestrator_agents_share_the_case_store_singleton() -> None:
    orchestrator = get_orchestrator()
    case_store = get_case_intelligence_workflow().case_store

    assert orchestrator._analysis_agent._case_store is case_store  # noqa: SLF001
    assert orchestrator._verifier_agent._case_store is case_store  # noqa: SLF001
    assert orchestrator._synthesis_agent._case_store is case_store  # noqa: SLF001


def test_get_orchestrator_agents_share_the_fabric_singleton() -> None:
    orchestrator = get_orchestrator()
    fabric = get_ai_intelligence_fabric()

    assert orchestrator._analysis_agent._fabric is fabric  # noqa: SLF001
    assert orchestrator._synthesis_agent._fabric is fabric  # noqa: SLF001


def test_get_orchestrator_agents_share_the_governance_singleton() -> None:
    orchestrator = get_orchestrator()
    governance = get_ai_governance_platform()

    assert orchestrator._analysis_agent._governance is governance  # noqa: SLF001
    assert orchestrator._synthesis_agent._governance is governance  # noqa: SLF001


def test_get_orchestrator_analysis_agent_shares_the_document_store_singleton() -> None:
    orchestrator = get_orchestrator()

    assert orchestrator._analysis_agent._document_store is get_document_store()  # noqa: SLF001


def test_orchestrator_without_arguments_keeps_its_own_unshared_defaults() -> None:
    """`Orchestrator()` built with no arguments must keep behaving exactly
    as before this sprint: its own private `AnalysisAgent`/`VerifierAgent`/
    `SynthesisAgent`, none of them shared with `get_orchestrator()`'s fully
    wired versions."""
    plain = Orchestrator()
    wired = get_orchestrator()

    assert plain._analysis_agent is not wired._analysis_agent  # noqa: SLF001
    assert plain._verifier_agent is not wired._verifier_agent  # noqa: SLF001
    assert plain._synthesis_agent is not wired._synthesis_agent  # noqa: SLF001
    assert plain._analysis_agent._fabric is None  # noqa: SLF001
    assert plain._analysis_agent._governance is None  # noqa: SLF001
