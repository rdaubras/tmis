from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowMonitoringSnapshot:
    """Aggregated view over `workflow_automation.metrics.
    WorkflowRunMetrics` (Sprint 17) — "workflows actifs, durée
    moyenne, erreurs, reprises, validations" (sprint requirement).
    Platform-wide, not per-firm: `WorkflowRunMetrics` carries no
    `firm_id` field today."""

    total_runs: int
    average_duration_ms: float
    total_errors: int
    total_retries: int
    total_validations: int
    total_cancellations: int
