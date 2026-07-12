from typing import Protocol

from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics


class WorkflowMetricsSinkPort(Protocol):
    def record(self, metrics: WorkflowRunMetrics) -> None: ...
