from tmis.cloud_operations.workflow_monitoring.ports import WorkflowMetricsReaderPort
from tmis.cloud_operations.workflow_monitoring.schemas import WorkflowMonitoringSnapshot


class WorkflowMonitoringEngine:
    """Composes `workflow_automation.metrics` (Sprint 17) directly
    rather than a second workflow-metrics ledger — that sink already
    carries every field the sprint asks for (durée, erreurs, reprises,
    validations, annulations); this engine only adds the aggregation
    across runs."""

    def __init__(self, sink: WorkflowMetricsReaderPort) -> None:
        self._sink = sink

    def snapshot(self) -> WorkflowMonitoringSnapshot:
        runs = self._sink.all()
        total = len(runs)
        average_duration = sum(r.duration_ms for r in runs) / total if total else 0.0
        return WorkflowMonitoringSnapshot(
            total_runs=total,
            average_duration_ms=average_duration,
            total_errors=sum(r.error_count for r in runs),
            total_retries=sum(r.retry_count for r in runs),
            total_validations=sum(r.validation_count for r in runs),
            total_cancellations=sum(r.cancellation_count for r in runs),
        )
