from tmis.legal_drafting.evaluation.metrics import DraftMetrics


class DraftEvaluator:
    """Collects `DraftMetrics` for every drafting run, mirroring
    `tmis.legal_reasoning.evaluation.ReasoningEvaluator` (see
    docs/28-legal-drafting.md — Observabilité)."""

    def __init__(self) -> None:
        self._history: list[DraftMetrics] = []

    def record(self, metrics: DraftMetrics) -> None:
        self._history.append(metrics)

    @property
    def history(self) -> list[DraftMetrics]:
        return list(self._history)

    def average_duration_ms(self) -> float:
        if not self._history:
            return 0.0
        return sum(m.duration_ms for m in self._history) / len(self._history)

    def total_estimated_cost_usd(self) -> float:
        return sum(m.estimated_cost_usd for m in self._history)
