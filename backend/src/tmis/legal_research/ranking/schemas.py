from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankingWeights:
    """Configurable weights for the five signals used by the Ranking
    Engine (see docs/23-guide-ranking-engine.md).

    "Relevance" is not a separate field: it is expressed as the weighted
    combination of `lexical` and `vector` below, so the two textual
    relevance signals are not double-counted against a third generic
    relevance weight.
    """

    lexical: float = 0.30
    vector: float = 0.30
    authority: float = 0.25
    freshness: float = 0.15

    def normalized(self) -> "RankingWeights":
        total = self.lexical + self.vector + self.authority + self.freshness
        if total <= 0:
            return RankingWeights(lexical=0.25, vector=0.25, authority=0.25, freshness=0.25)
        return RankingWeights(
            lexical=self.lexical / total,
            vector=self.vector / total,
            authority=self.authority / total,
            freshness=self.freshness / total,
        )
