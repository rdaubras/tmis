from typing import Protocol

from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics


class WorkflowMetricsReaderPort(Protocol):
    """Read-side of `workflow_automation.metrics.
    WorkflowMetricsSinkPort` — that port is write-only (`.record()`),
    but `workflow_automation.metrics.sinks.InMemoryWorkflowMetricsSink`
    also exposes `.all()`, which this engine needs to aggregate. A
    narrow read port avoids widening the write-side port with a
    method callers who only ever write never need."""

    def all(self) -> list[WorkflowRunMetrics]: ...
