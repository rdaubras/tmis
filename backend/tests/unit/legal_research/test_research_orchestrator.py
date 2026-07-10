import pytest

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import RelevanceScores
from tmis.legal_research.sources.registry import SourceRegistry

_DOCS = [
    ConnectorDocument(
        id="civ-1240",
        title="Code civil, article 1240",
        content="Tout fait quelconque de l'homme, qui cause à autrui un dommage.",
        connector="codes",
        metadata={"article": "1240", "date": "1804-01-01"},
    ),
    ConnectorDocument(
        id="doctrine-1",
        title="Chronique responsabilité",
        content="Analyse doctrinale du dommage et de la responsabilité.",
        connector="doctrine",
        metadata={"date": "2020-01-01"},
    ),
]


class _FakeSearch:
    def __init__(self) -> None:
        self.call_count = 0

    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        self.call_count += 1
        scores = {
            "civ-1240": RelevanceScores(lexical_score=0.9, vector_score=0.8),
            "doctrine-1": RelevanceScores(lexical_score=0.2, vector_score=0.3),
        }
        return list(_DOCS), ["codes", "doctrine"], scores


def _build_orchestrator(search: _FakeSearch) -> ResearchOrchestrator:
    return ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=search,
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026),
        citation_engine=CitationEngine(),
        cache=ResearchCache(InMemoryCache()),
        history=InMemoryResearchHistory(),
        evaluator=ResearchEvaluator(),
    )


@pytest.mark.asyncio
async def test_search_returns_ranked_results_with_citations() -> None:
    orchestrator = _build_orchestrator(_FakeSearch())

    response = await orchestrator.search("responsabilité")

    assert len(response.results) == 2
    citations = orchestrator.get_citations(response.search_id)
    assert citations is not None
    assert len(citations) == 2
    assert response.cache_hit is False


@pytest.mark.asyncio
async def test_search_results_are_sorted_by_final_score() -> None:
    orchestrator = _build_orchestrator(_FakeSearch())
    response = await orchestrator.search("responsabilité")
    scores = [r.final_score for r in response.results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_second_identical_search_hits_the_ranking_cache() -> None:
    search = _FakeSearch()
    orchestrator = _build_orchestrator(search)

    await orchestrator.search("responsabilité")
    second = await orchestrator.search("responsabilité")

    assert search.call_count == 1
    assert second.cache_hit is True


@pytest.mark.asyncio
async def test_get_response_retrieves_a_past_search() -> None:
    orchestrator = _build_orchestrator(_FakeSearch())
    response = await orchestrator.search("responsabilité")

    retrieved = orchestrator.get_response(response.search_id)

    assert retrieved is response


@pytest.mark.asyncio
async def test_get_response_returns_none_for_unknown_id() -> None:
    orchestrator = _build_orchestrator(_FakeSearch())
    assert orchestrator.get_response("unknown") is None


@pytest.mark.asyncio
async def test_search_records_history_entry() -> None:
    orchestrator = _build_orchestrator(_FakeSearch())
    await orchestrator.search("responsabilité", user_id="user-1", case_id="case-1")

    entries = orchestrator.history.list_for_user("user-1")

    assert len(entries) == 1
    assert entries[0].case_id == "case-1"


@pytest.mark.asyncio
async def test_search_records_evaluation_metrics() -> None:
    evaluator = ResearchEvaluator()
    orchestrator = ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=_FakeSearch(),
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026),
        citation_engine=CitationEngine(),
        cache=ResearchCache(InMemoryCache()),
        history=InMemoryResearchHistory(),
        evaluator=evaluator,
    )

    await orchestrator.search("responsabilité")

    assert len(evaluator.history) == 1
    assert evaluator.history[0].result_count == 2
