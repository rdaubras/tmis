from tmis.legal_reasoning.evaluation.metrics import ReasoningMetrics


class ReasoningEvaluator:
    """Collects `ReasoningMetrics` for every reasoning run, mirroring
    `tmis.legal_research.evaluation.ResearchEvaluator` (see
    docs/25-legal-reasoning.md — Observabilité)."""

    def __init__(self) -> None:
        self._history: list[ReasoningMetrics] = []

    def record(self, metrics: ReasoningMetrics) -> None:
        self._history.append(metrics)

    @property
    def history(self) -> list[ReasoningMetrics]:
        return list(self._history)

    def average_duration_ms(self) -> float:
        if not self._history:
            return 0.0
        return sum(m.duration_ms for m in self._history) / len(self._history)
