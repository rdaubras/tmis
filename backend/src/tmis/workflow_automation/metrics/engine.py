from tmis.workflow_automation.metrics.ports import WorkflowMetricsSinkPort
from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics


class WorkflowMetricsEngine:
    """Fans a `WorkflowRunMetrics` reading out to every registered
    sink — same sink-fanout extensibility as
    `ai_governance.evaluation.GovernanceEvaluator` and
    `strategic_intelligence.evaluation.StrategicIntelligenceEvaluator`."""

    def __init__(self, sinks: list[WorkflowMetricsSinkPort] | None = None) -> None:
        self._sinks = list(sinks) if sinks is not None else []

    def record(self, metrics: WorkflowRunMetrics) -> None:
        for sink in self._sinks:
            sink.record(metrics)
