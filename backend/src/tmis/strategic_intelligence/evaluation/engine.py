from tmis.strategic_intelligence.evaluation.ports import StrategicMetricsSinkPort
from tmis.strategic_intelligence.evaluation.schemas import StrategyGenerationMetrics


class StrategicIntelligenceEvaluator:
    """Fans a `StrategyGenerationMetrics` reading out to every
    registered sink — same sink-fanout extensibility as
    `ai_governance.evaluation.GovernanceEvaluator`."""

    def __init__(self, sinks: list[StrategicMetricsSinkPort] | None = None) -> None:
        self._sinks = list(sinks) if sinks is not None else []

    def record(self, metrics: StrategyGenerationMetrics) -> None:
        for sink in self._sinks:
            sink.record(metrics)
