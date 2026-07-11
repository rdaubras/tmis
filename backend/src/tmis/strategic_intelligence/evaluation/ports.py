from typing import Protocol

from tmis.strategic_intelligence.evaluation.schemas import StrategyGenerationMetrics


class StrategicMetricsSinkPort(Protocol):
    def record(self, metrics: StrategyGenerationMetrics) -> None: ...
