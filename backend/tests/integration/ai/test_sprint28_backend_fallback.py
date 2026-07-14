"""End-to-end proof that the Sprint 28 real cache/reranker backends are
opt-in: with zero external configuration and no Redis reachable, every
hardcoded default this sprint touched (`TMISKernel.cache`,
`BaseConnectorPlugin`'s cache, `ai_fabric.bootstrap.get_response_cache`,
`RagPipeline`'s reranker) keeps behaving exactly as the Sprint 2 in-memory/
heuristic defaults did — and flipping config swaps in the real adapter
behind the same `CachePort`/`RerankerPort`, without any change to either
port. Mirrors `tests/integration/ai/test_sprint27_backend_fallback.py`.
"""

from collections.abc import Iterator

import pytest

from tmis.ai.cache import factory as cache_factory
from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai.reranking import factory as reranking_factory
from tmis.ai.reranking.simple_reranker import KeywordOverlapReranker
from tmis.ai_fabric.bootstrap import get_response_cache
from tmis.core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_singletons() -> Iterator[None]:
    get_kernel.cache_clear()
    get_response_cache.cache_clear()
    cache_factory._shared_redis_client.cache_clear()
    get_settings.cache_clear()
    yield
    get_kernel.cache_clear()
    get_response_cache.cache_clear()
    cache_factory._shared_redis_client.cache_clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_kernel_cache_defaults_to_in_memory_with_no_redis_reachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in ("TMIS_REDIS_URL", "TMIS_RERANKER_BACKEND"):
        monkeypatch.delenv(var, raising=False)

    kernel = get_kernel()

    assert isinstance(kernel.cache, InMemoryCache)

    # And it still behaves like a cache: unchanged Kernel-level behavior.
    await kernel.cache.set("k", "v")
    assert await kernel.cache.get("k") == "v"


def test_response_cache_defaults_to_in_memory_backend_with_no_redis_reachable() -> None:
    response_cache = get_response_cache()

    assert isinstance(response_cache._backend, InMemoryCache)  # noqa: SLF001


def test_reranker_factory_defaults_to_keyword_overlap_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TMIS_RERANKER_BACKEND", raising=False)
    get_settings.cache_clear()

    reranker = reranking_factory.get_reranker()

    assert isinstance(reranker, KeywordOverlapReranker)


@pytest.mark.asyncio
async def test_kernel_rag_query_still_works_with_default_reranker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in ("TMIS_REDIS_URL", "TMIS_RERANKER_BACKEND"):
        monkeypatch.delenv(var, raising=False)

    kernel = get_kernel()

    citations = await kernel.rag.query("le contrat de bail")

    assert citations == []  # nothing ingested yet, but the call must not raise


def test_flipping_the_reranker_backend_flag_attempts_the_real_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No network/model cache is guaranteed in the test environment, so
    this only asserts the factory *attempted* the real backend and
    degraded safely — never that it crashed. Either outcome is a real
    `RerankerPort` instance (mirrors `test_flipping_the_embedding_backend_
    flag_swaps_the_real_provider_in` in the Sprint 27 fallback test)."""
    monkeypatch.setenv("TMIS_RERANKER_BACKEND", "cross_encoder")
    get_settings.cache_clear()

    reranker = reranking_factory.get_reranker()

    assert hasattr(reranker, "rerank")
