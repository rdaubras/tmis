import uuid

import pytest

from tmis.agents.bootstrap import get_orchestrator
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.case_intelligence.bootstrap import clear_case_intelligence_caches

_FIRM_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Every composition root touched by this module is an `lru_cache`d
    process-wide singleton; reset them before each test so identity
    assertions never depend on what a previous test constructed first —
    same pattern as `tests/unit/document_intelligence/test_bootstrap.py`
    (Sprint 37). `get_orchestrator` is no longer one of them
    (ADR-CASEINT-01, docs/19-case-intelligence.md), and neither is
    `document_intelligence.bootstrap.get_document_store` (ADR-DOCINT-01,
    docs/14-document-intelligence.md) — both are assembled fresh, per
    `firm_id`, on every call."""
    get_kernel.cache_clear()
    get_ai_intelligence_fabric.cache_clear()
    get_ai_governance_platform.cache_clear()
    clear_case_intelligence_caches()


def test_get_orchestrator_agents_share_one_case_store_per_call() -> None:
    """`get_orchestrator(firm_id)` is no longer a singleton (ADR-CASEINT-01)
    — a fresh `Orchestrator` is built on every call — but within one call,
    its three agents must still all read and write the exact same
    `CaseStorePort` instance, or an analysis run would silently stop
    seeing what another of its own agents just wrote."""
    orchestrator = get_orchestrator(_FIRM_ID)

    case_store = orchestrator._analysis_agent._case_store  # noqa: SLF001
    assert orchestrator._verifier_agent._case_store is case_store  # noqa: SLF001
    assert orchestrator._synthesis_agent._case_store is case_store  # noqa: SLF001


def test_get_orchestrator_agents_share_the_kernel_singleton() -> None:
    orchestrator = get_orchestrator(_FIRM_ID)
    kernel = get_kernel()

    assert orchestrator._analysis_agent._kernel is kernel  # noqa: SLF001
    assert orchestrator._synthesis_agent._kernel is kernel  # noqa: SLF001


def test_get_orchestrator_agents_share_the_fabric_singleton() -> None:
    orchestrator = get_orchestrator(_FIRM_ID)
    fabric = get_ai_intelligence_fabric()

    assert orchestrator._analysis_agent._fabric is fabric  # noqa: SLF001
    assert orchestrator._synthesis_agent._fabric is fabric  # noqa: SLF001


def test_get_orchestrator_agents_share_the_governance_singleton() -> None:
    orchestrator = get_orchestrator(_FIRM_ID)
    governance = get_ai_governance_platform()

    assert orchestrator._analysis_agent._governance is governance  # noqa: SLF001
    assert orchestrator._synthesis_agent._governance is governance  # noqa: SLF001


def test_get_orchestrator_analysis_agent_uses_the_firm_scoped_document_store() -> None:
    orchestrator = get_orchestrator(_FIRM_ID)

    assert orchestrator._analysis_agent._document_store._firm_id == str(_FIRM_ID)  # noqa: SLF001


def test_orchestrator_without_arguments_keeps_its_own_unshared_defaults() -> None:
    """`Orchestrator()` built with no arguments must keep behaving exactly
    as before this sprint: its own private `AnalysisAgent`/`VerifierAgent`/
    `SynthesisAgent`, none of them shared with `get_orchestrator()`'s fully
    wired versions."""
    plain = Orchestrator()
    wired = get_orchestrator(_FIRM_ID)

    assert plain._analysis_agent is not wired._analysis_agent  # noqa: SLF001
    assert plain._verifier_agent is not wired._verifier_agent  # noqa: SLF001
    assert plain._synthesis_agent is not wired._synthesis_agent  # noqa: SLF001
    assert plain._analysis_agent._fabric is None  # noqa: SLF001
    assert plain._analysis_agent._governance is None  # noqa: SLF001
