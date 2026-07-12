from tmis.integration_hub.monitoring.ports import ConnectorMetricsSinkPort
from tmis.integration_hub.monitoring.schemas import ConnectorOperationMetric


class ConnectorMonitoringEngine:
    """Implements
    `connector_framework.ports.ConnectorMetricsRecorderPort` by
    fanning a reading out to every registered sink — same fanout
    pattern as `workflow_automation.metrics.WorkflowMetricsEngine`.
    Structurally satisfies the decoupled port `ConnectorInvoker` was
    built against, without `connector_framework` importing this
    module — "surveiller : latence, taux d'erreur, volumes échangés"
    (sprint requirement)."""

    def __init__(self, sinks: list[ConnectorMetricsSinkPort] | None = None) -> None:
        self._sinks = list(sinks) if sinks is not None else []

    def record(
        self,
        connector_id: str,
        firm_id: str,
        operation: str,
        *,
        success: bool,
        duration_ms: float,
        record_count: int = 0,
        error: str | None = None,
    ) -> None:
        metric = ConnectorOperationMetric(
            connector_id=connector_id,
            firm_id=firm_id,
            operation=operation,
            success=success,
            duration_ms=duration_ms,
            record_count=record_count,
            error=error,
        )
        for sink in self._sinks:
            sink.record(metric)
