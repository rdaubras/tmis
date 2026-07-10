from collections.abc import Callable
from datetime import UTC, datetime

from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.schemas import ResearchResult
from tmis.legal_research.sources.registry import SourceRegistry

_MAX_AGE_YEARS = 50.0
_NEUTRAL_FRESHNESS = 0.3


class ConfigurableRanker:
    """Implements `RankingPort`: scores each result on relevance
    (lexical + vector), source authority, and freshness, then combines
    them with `RankingWeights` (see docs/23-guide-ranking-engine.md).
    """

    def __init__(
        self,
        source_registry: SourceRegistry | None = None,
        *,
        current_year_fn: Callable[[], int] | None = None,
    ) -> None:
        self._source_registry = source_registry or SourceRegistry()
        self._current_year_fn = current_year_fn or (lambda: datetime.now(UTC).year)

    def rank(
        self, results: list[ResearchResult], weights: RankingWeights | None = None
    ) -> list[ResearchResult]:
        effective_weights = (weights or RankingWeights()).normalized()
        for result in results:
            result.authority_score = self._source_registry.authority_score(result.connector)
            result.freshness_score = self._freshness_score(result.date)
            result.final_score = (
                effective_weights.lexical * result.lexical_score
                + effective_weights.vector * result.vector_score
                + effective_weights.authority * result.authority_score
                + effective_weights.freshness * result.freshness_score
            )
        return sorted(results, key=lambda r: r.final_score, reverse=True)

    def _freshness_score(self, date: str | None) -> float:
        if not date or len(date) < 4 or not date[:4].isdigit():
            return _NEUTRAL_FRESHNESS
        year = int(date[:4])
        age_years = max(0, self._current_year_fn() - year)
        return max(0.0, 1.0 - age_years / _MAX_AGE_YEARS)
