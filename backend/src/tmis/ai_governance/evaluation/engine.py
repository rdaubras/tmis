from tmis.ai_governance.evaluation.ports import GovernanceMetricsSinkPort
from tmis.ai_governance.evaluation.schemas import GovernanceRunMetrics


class GovernanceEvaluator:
    """Fans a `GovernanceRunMetrics` reading out to every registered
    sink — mirrors `tmis.ai.evaluation.evaluator.Evaluator`'s
    sink-fanout extensibility so a new metrics destination (e.g. a
    future Prometheus sink) can be added without touching callers."""

    def __init__(self, sinks: list[GovernanceMetricsSinkPort] | None = None) -> None:
        self._sinks = list(sinks) if sinks is not None else []

    def record(self, metrics: GovernanceRunMetrics) -> None:
        for sink in self._sinks:
            sink.record(metrics)
