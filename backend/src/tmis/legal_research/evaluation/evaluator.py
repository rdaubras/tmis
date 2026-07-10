from tmis.legal_research.evaluation.metrics import ResearchMetrics


class ResearchEvaluator:
    """Collects `ResearchMetrics` for every research run, mirroring
    `tmis.case_intelligence.evaluation.CaseEvaluator` (see
    docs/21-legal-research.md — Évaluation)."""

    def __init__(self) -> None:
        self._history: list[ResearchMetrics] = []

    def record(self, metrics: ResearchMetrics) -> None:
        self._history.append(metrics)

    @property
    def history(self) -> list[ResearchMetrics]:
        return list(self._history)

    def cache_hit_rate(self) -> float:
        if not self._history:
            return 0.0
        return sum(1 for m in self._history if m.cache_hit) / len(self._history)

    def average_search_time_ms(self) -> float:
        if not self._history:
            return 0.0
        return sum(m.search_time_ms for m in self._history) / len(self._history)
