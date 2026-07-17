import uuid

import pytest

from tmis.agents.bootstrap import get_contract_agent
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.document_intelligence.bootstrap import (
    get_document_knowledge_graph,
    get_document_pipeline,
    get_document_store,
)

_FIRM_ID = uuid.uuid4()
_OTHER_FIRM_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """`get_document_knowledge_graph` is the one remaining `lru_cache`d,
    firm-partitioned singleton this module owns (ADR-DOCINT-01,
    docs/14-document-intelligence.md) — `get_document_store`/
    `get_document_pipeline`/`get_contract_agent` are no longer cached at
    all (built fresh, per `firm_id`, on every call), so there is nothing
    to clear for them."""
    get_document_knowledge_graph.cache_clear()
    get_kernel.cache_clear()


def test_get_document_store_is_scoped_to_the_given_firm() -> None:
    store = get_document_store(_FIRM_ID)

    assert store._firm_id == str(_FIRM_ID)  # noqa: SLF001


def test_get_document_pipeline_shares_the_firm_scoped_document_store() -> None:
    pipeline = get_document_pipeline(_FIRM_ID)

    assert pipeline.document_store._firm_id == str(_FIRM_ID)  # noqa: SLF001


def test_get_document_pipeline_uses_the_firm_partitioned_knowledge_graph() -> None:
    pipeline = get_document_pipeline(_FIRM_ID)

    assert pipeline.knowledge_graph is get_document_knowledge_graph(_FIRM_ID)


def test_get_document_knowledge_graph_is_partitioned_per_firm() -> None:
    assert get_document_knowledge_graph(_FIRM_ID) is get_document_knowledge_graph(_FIRM_ID)
    assert get_document_knowledge_graph(_FIRM_ID) is not get_document_knowledge_graph(
        _OTHER_FIRM_ID
    )


def test_get_contract_agent_shares_the_firm_scoped_document_store() -> None:
    agent = get_contract_agent(_FIRM_ID)

    assert agent._document_store._firm_id == str(_FIRM_ID)  # noqa: SLF001, SLF001


def test_orchestrator_without_arguments_does_not_reach_for_the_real_document_store() -> None:
    """`Orchestrator()` built with no arguments has no `firm_id` to scope
    a real `SQLAlchemyDocumentStore` with (ADR-DOCINT-01,
    docs/14-document-intelligence.md) — it must fall back to
    `AnalysisAgent`'s own private, unshared `InMemoryDocumentStore`
    default, never the firm-scoped real store `agents.bootstrap.
    get_orchestrator(firm_id)` wires."""
    orchestrator = Orchestrator()

    assert not hasattr(orchestrator._analysis_agent._document_store, "_firm_id")  # noqa: SLF001
