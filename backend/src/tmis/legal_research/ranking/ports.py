from typing import Protocol

from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.schemas import ResearchResult


class RankingPort(Protocol):
    """Port implemented by every interchangeable ranking engine."""

    def rank(
        self, results: list[ResearchResult], weights: RankingWeights | None = None
    ) -> list[ResearchResult]: ...
