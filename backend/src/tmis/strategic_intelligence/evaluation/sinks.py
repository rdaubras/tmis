from tmis.strategic_intelligence.evaluation.schemas import StrategyGenerationMetrics


class InMemoryStrategicMetricsSink:
    def __init__(self) -> None:
        self._metrics: list[StrategyGenerationMetrics] = []

    def record(self, metrics: StrategyGenerationMetrics) -> None:
        self._metrics.append(metrics)

    def all(self) -> list[StrategyGenerationMetrics]:
        return list(self._metrics)
