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
    cache = ResearchCache(InMemoryCache())
    assert await cache.get_raw_search("licenciement", None) is None


@pytest.mark.asyncio
async def test_raw_search_cache_round_trip_reconstructs_dataclasses() -> None:
    cache = ResearchCache(InMemoryCache())
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
    cache = ResearchCache(InMemoryCache())
    results = [_result("r1"), _result("r2")]

    await cache.set_normalized("licenciement", None, results)
    retrieved = await cache.get_normalized("licenciement", None)

    assert retrieved is not None
    assert [r.id for r in retrieved] == ["r1", "r2"]


@pytest.mark.asyncio
async def test_ranking_cache_is_keyed_by_weights() -> None:
    cache = ResearchCache(InMemoryCache())
    results = [_result("r1")]
    weights_a = RankingWeights(lexical=1.0, vector=0.0, authority=0.0, freshness=0.0)
    weights_b = RankingWeights(lexical=0.0, vector=1.0, authority=0.0, freshness=0.0)

    await cache.set_ranking("licenciement", None, weights_a, results)

    assert await cache.get_ranking("licenciement", None, weights_a) is not None
    assert await cache.get_ranking("licenciement", None, weights_b) is None


@pytest.mark.asyncio
async def test_raw_search_cache_is_keyed_by_connector_names() -> None:
    cache = ResearchCache(InMemoryCache())
    doc = ConnectorDocument(id="d1", title="T", content="C", connector="codes")
    entry = RawSearchCacheEntry(documents=(doc,), connectors_used=("codes",), scores={})

    await cache.set_raw_search("licenciement", ["codes"], entry)

    assert await cache.get_raw_search("licenciement", ["codes"]) is not None
    assert await cache.get_raw_search("licenciement", ["doctrine"]) is None
    assert await cache.get_raw_search("licenciement", None) is None
