import time
import uuid
from datetime import UTC, datetime

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.cache.schemas import RawSearchCacheEntry
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.evaluation.metrics import ResearchMetrics
from tmis.legal_research.history.ports import ResearchHistoryPort
from tmis.legal_research.history.schemas import ResearchHistoryEntry
from tmis.legal_research.normalization.ports import SourceNormalizerPort
from tmis.legal_research.queries.ports import QueryEnginePort
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.ranking.ports import RankingPort
from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.ports import ResearchSearchPort
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResponse, ResearchResult


class ResearchOrchestrator:
    """The Research Orchestrator (see docs/21-legal-research.md):
    receives a query, prepares it via the Query Engine, executes the
    search, merges/deduplicates/normalizes results, ranks them, attaches
    citations, records history and evaluation metrics — checking the
    three-layer cache at each stage so a repeated query short-circuits as
    early as possible.

    This class never talks to a model provider or a connector itself: it
    only calls the ports it was constructed with.
    """

    def __init__(
        self,
        *,
        query_engine: QueryEnginePort,
        search: ResearchSearchPort,
        normalizer: SourceNormalizerPort,
        ranker: RankingPort,
        citation_engine: CitationEngine,
        cache: ResearchCache,
        history: ResearchHistoryPort,
        evaluator: ResearchEvaluator,
    ) -> None:
        self._query_engine = query_engine
        self._search = search
        self._normalizer = normalizer
        self._ranker = ranker
        self._citation_engine = citation_engine
        self._cache = cache
        self._history = history
        self._evaluator = evaluator
        self._responses: dict[str, ResearchResponse] = {}
        self._citations: dict[str, tuple[ResearchCitation, ...]] = {}

    async def search(
        self,
        raw_text: str,
        *,
        filters: dict[str, object] | None = None,
        connector_names: list[str] | None = None,
        weights: RankingWeights | None = None,
        user_id: str | None = None,
        case_id: str | None = None,
    ) -> ResearchResponse:
        start = time.perf_counter()
        query = self._query_engine.build(raw_text, filters)
        effective_weights = weights or RankingWeights()

        ranked, cache_hit, duplicate_rate = await self._resolve_ranked_results(
            query, connector_names, effective_weights
        )

        duration_ms = (time.perf_counter() - start) * 1000
        connectors_used = tuple(sorted({r.connector for r in ranked}))
        search_id = str(uuid.uuid4())

        response = ResearchResponse(
            search_id=search_id,
            query=raw_text,
            results=tuple(ranked),
            connectors_used=connectors_used,
            duration_ms=duration_ms,
            cache_hit=cache_hit,
        )
        citations = tuple(self._citation_engine.build(r) for r in ranked)
        self._responses[search_id] = response
        self._citations[search_id] = citations

        self._evaluator.record(
            ResearchMetrics(
                search_id=search_id,
                query=raw_text,
                search_time_ms=duration_ms,
                source_count=len(connectors_used),
                result_count=len(ranked),
                duplicate_rate=duplicate_rate,
                cache_hit=cache_hit,
                connectors_used=connectors_used,
            )
        )
        self._history.record(
            ResearchHistoryEntry(
                id=search_id,
                query_text=raw_text,
                timestamp=datetime.now(UTC),
                connectors_used=connectors_used,
                duration_ms=duration_ms,
                result_count=len(ranked),
                user_id=user_id,
                case_id=case_id,
            )
        )
        return response

    async def _resolve_ranked_results(
        self,
        query: ResearchQuery,
        connector_names: list[str] | None,
        weights: RankingWeights,
    ) -> tuple[list[ResearchResult], bool, float]:
        cached_ranking = await self._cache.get_ranking(query.search_text, connector_names, weights)
        if cached_ranking is not None:
            return cached_ranking, True, 0.0

        normalized, normalized_cache_hit, duplicate_rate = await self._resolve_normalized(
            query, connector_names
        )
        ranked = self._ranker.rank(normalized, weights)
        await self._cache.set_ranking(query.search_text, connector_names, weights, ranked)
        return ranked, normalized_cache_hit, duplicate_rate

    async def _resolve_normalized(
        self, query: ResearchQuery, connector_names: list[str] | None
    ) -> tuple[list[ResearchResult], bool, float]:
        cached_normalized = await self._cache.get_normalized(query.search_text, connector_names)
        if cached_normalized is not None:
            return cached_normalized, True, 0.0

        documents, scores, raw_cache_hit = await self._resolve_raw(query, connector_names)
        normalized = self._normalizer.normalize(documents, scores=scores)
        await self._cache.set_normalized(query.search_text, connector_names, normalized)
        duplicate_rate = 0.0 if not documents else 1 - (len(normalized) / len(documents))
        return normalized, raw_cache_hit, duplicate_rate

    async def _resolve_raw(
        self, query: ResearchQuery, connector_names: list[str] | None
    ) -> tuple[list[ConnectorDocument], dict[str, RelevanceScores], bool]:
        cached_raw = await self._cache.get_raw_search(query.search_text, connector_names)
        if cached_raw is not None:
            return list(cached_raw.documents), cached_raw.scores, True

        documents, connectors_used, scores = await self._search.execute(
            query, connector_names=connector_names
        )
        await self._cache.set_raw_search(
            query.search_text,
            connector_names,
            RawSearchCacheEntry(
                documents=tuple(documents), connectors_used=tuple(connectors_used), scores=scores
            ),
        )
        return documents, scores, False

    def get_response(self, search_id: str) -> ResearchResponse | None:
        return self._responses.get(search_id)

    def get_citations(self, search_id: str) -> tuple[ResearchCitation, ...] | None:
        return self._citations.get(search_id)

    @property
    def history(self) -> ResearchHistoryPort:
        return self._history
