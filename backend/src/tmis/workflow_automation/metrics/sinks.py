from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics


class InMemoryWorkflowMetricsSink:
    def __init__(self) -> None:
        self._metrics: list[WorkflowRunMetrics] = []

    def record(self, metrics: WorkflowRunMetrics) -> None:
        self._metrics.append(metrics)

    def all(self) -> list[WorkflowRunMetrics]:
        return list(self._metrics)
