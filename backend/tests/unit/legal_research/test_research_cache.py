import pytest

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.cache.schemas import RawSearchCacheEntry
from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResult


def _result(result_id: str = "r1") -> ResearchResult:
    return ResearchResult(
        id=result_id,
        title="Title",
        excerpt="Excerpt",
        connector="codes",
        document_type="code",
        reference="ref",
        date="2020-01-01",
    )


@pytest.mark.asyncio
async def test_raw_search_cache_miss_returns_none() -> None:
    cache = ResearchCache(InMemoryCache(), "firm-1")
    assert await cache.get_raw_search("licenciement", None) is None


@pytest.mark.asyncio
async def test_raw_search_cache_round_trip_reconstructs_dataclasses() -> None:
    cache = ResearchCache(InMemoryCache(), "firm-1")
    doc = ConnectorDocument(id="d1", title="T", content="C", connector="codes")
    entry = RawSearchCacheEntry(
        documents=(doc,),
        connectors_used=("codes",),
        scores={"d1": RelevanceScores(lexical_score=0.5, vector_score=0.7)},
    )

    await cache.set_raw_search("licenciement", None, entry)
    retrieved = await cache.get_raw_search("licenciement", None)

    assert retrieved is not None
    assert retrieved.documents == (doc,)
    assert retrieved.connectors_used == ("codes",)
    assert retrieved.scores["d1"].lexical_score == 0.5


@pytest.mark.asyncio
async def test_normalized_cache_round_trip() -> None:
    cache = ResearchCache(InMemoryCache(), "firm-1")
    results = [_result("r1"), _result("r2")]

    await cache.set_normalized("licenciement", None, results)
    retrieved = await cache.get_normalized("licenciement", None)

    assert retrieved is not None
    assert [r.id for r in retrieved] == ["r1", "r2"]


@pytest.mark.asyncio
async def test_ranking_cache_is_keyed_by_weights() -> None:
    cache = ResearchCache(InMemoryCache(), "firm-1")
    results = [_result("r1")]
    weights_a = RankingWeights(lexical=1.0, vector=0.0, authority=0.0, freshness=0.0)
    weights_b = RankingWeights(lexical=0.0, vector=1.0, authority=0.0, freshness=0.0)

    await cache.set_ranking("licenciement", None, weights_a, results)

    assert await cache.get_ranking("licenciement", None, weights_a) is not None
    assert await cache.get_ranking("licenciement", None, weights_b) is None


@pytest.mark.asyncio
async def test_raw_search_cache_is_keyed_by_connector_names() -> None:
    cache = ResearchCache(InMemoryCache(), "firm-1")
    doc = ConnectorDocument(id="d1", title="T", content="C", connector="codes")
    entry = RawSearchCacheEntry(documents=(doc,), connectors_used=("codes",), scores={})

    await cache.set_raw_search("licenciement", ["codes"], entry)

    assert await cache.get_raw_search("licenciement", ["codes"]) is not None
    assert await cache.get_raw_search("licenciement", ["doctrine"]) is None
    assert await cache.get_raw_search("licenciement", None) is None


# ADR-RESEARCH-01 (docs/21-legal-research.md): `firm_id` is prefixed into
# every key this class builds, at all three cache layers — a shared
# backend (here `InMemoryCache`, in production the Kernel's Redis-backed
# `CachePort`) must never let firm B's identical query return firm A's
# cached results, since a connector's results can be private to A's
# subscription.
@pytest.mark.asyncio
async def test_raw_search_cache_is_isolated_by_firm() -> None:
    backend = InMemoryCache()
    cache_a = ResearchCache(backend, "firm-a")
    cache_b = ResearchCache(backend, "firm-b")
    doc = ConnectorDocument(id="d1", title="T", content="C", connector="private_database")
    entry = RawSearchCacheEntry(documents=(doc,), connectors_used=("private_database",), scores={})

    await cache_a.set_raw_search("non-concurrence", None, entry)

    assert await cache_a.get_raw_search("non-concurrence", None) is not None
    assert await cache_b.get_raw_search("non-concurrence", None) is None


@pytest.mark.asyncio
async def test_normalized_and_ranking_caches_are_isolated_by_firm() -> None:
    backend = InMemoryCache()
    cache_a = ResearchCache(backend, "firm-a")
    cache_b = ResearchCache(backend, "firm-b")
    results = [_result("r1")]
    weights = RankingWeights(lexical=1.0, vector=0.0, authority=0.0, freshness=0.0)

    await cache_a.set_normalized("non-concurrence", None, results)
    await cache_a.set_ranking("non-concurrence", None, weights, results)

    assert await cache_b.get_normalized("non-concurrence", None) is None
    assert await cache_b.get_ranking("non-concurrence", None, weights) is None
