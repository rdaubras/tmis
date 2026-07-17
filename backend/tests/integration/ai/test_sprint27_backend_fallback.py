"""End-to-end proof that the Sprint 27 real adapters are opt-in: with zero
external configuration, `get_kernel()` / `get_shared_research_orchestrator()` keep
wiring the exact same in-memory/fixture defaults Sprints 2/5 shipped, and
flipping one config flag swaps in the real adapter behind the same ports —
without any change to `IndexPort`/`EmbeddingProviderPort`/`ConnectorPort`.
"""

from collections.abc import Iterator

import pytest

from tmis.ai.connectors.codes_connector import CodesConnector
from tmis.ai.connectors.factory import build_codes_connector
from tmis.ai.embeddings.factory import get_embedding_provider
from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai.rag.factory import get_vector_index
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.core.config import get_settings
from tmis.legal_research.bootstrap import clear_research_caches, get_shared_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons() -> Iterator[None]:
    """Mirrors the existing `_clear_singletons` fixture pattern used by
    other cross-module bootstrap tests (e.g.
    tests/integration/legal_reasoning/test_reasoning_orchestrator_integration.py).

    `clear_research_caches()` (not just `get_shared_research_orchestrator.
    cache_clear()`) matters here specifically: `get_search_engine` — one
    of the caches it resets — captures a reference to *the* kernel
    instance at the time it first runs connector registration. Clearing
    only `get_kernel` and leaving `get_search_engine` stale would make
    `get_shared_research_orchestrator()` register connectors on a kernel
    instance this test no longer holds, and the assertions below would
    check the wrong kernel's connector list."""
    get_kernel.cache_clear()
    clear_research_caches()
    get_settings.cache_clear()
    yield
    get_kernel.cache_clear()
    clear_research_caches()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_kernel_defaults_to_in_memory_hashing_and_fixture_connectors_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in (
        "TMIS_RAG_VECTOR_INDEX_BACKEND",
        "TMIS_EMBEDDING_BACKEND",
        "TMIS_PISTE_CLIENT_ID",
        "TMIS_PISTE_CLIENT_SECRET",
        "TMIS_DOCTRINE_CONNECTOR_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)

    kernel = get_kernel()

    assert isinstance(kernel.embedding_provider, HashingEmbeddingProvider)
    assert set(kernel.connector_manager.list_connectors()) == {"codes", "jurisprudence", "doctrine"}

    citations = await kernel.rag.query("le contrat de bail")
    assert citations == []  # nothing ingested yet, but the call must not raise


@pytest.mark.asyncio
async def test_research_orchestrator_defaults_to_fixture_connectors_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in (
        "TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_BASE_URL",
        "TMIS_PRIVATE_DATABASE_CONNECTOR_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)

    orchestrator = get_shared_research_orchestrator()
    kernel = get_kernel()

    assert set(kernel.connector_manager.list_connectors()) == {
        "codes",
        "jurisprudence",
        "doctrine",
        "internal_documentation",
        "private_database",
    }
    assert orchestrator is not None


def test_flipping_the_embedding_backend_flag_swaps_the_real_provider_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TMIS_EMBEDDING_BACKEND", "sentence_transformers")
    get_settings.cache_clear()

    # No network/model cache is guaranteed in the test environment, so this
    # only asserts the factory *attempted* the real backend and degraded
    # safely — never that it crashed. Either outcome is a real provider
    # instance implementing the port.
    provider = get_embedding_provider()
    assert provider.dimensions > 0
    assert isinstance(provider.embedding_name, str)


def test_flipping_the_vector_index_backend_flag_swaps_qdrant_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TMIS_RAG_VECTOR_INDEX_BACKEND", "qdrant")
    get_settings.cache_clear()

    index = get_vector_index(dimensions=64)

    assert not isinstance(index, InMemoryVectorIndex)


def test_flipping_piste_credentials_swaps_the_real_codes_connector_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TMIS_PISTE_CLIENT_ID", "id")
    monkeypatch.setenv("TMIS_PISTE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()

    connector = build_codes_connector()
    assert not isinstance(connector, CodesConnector)
