from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class WorkflowRunMetrics:
    """Operational telemetry about one workflow execution — "tracer :
    workflows exécutés, temps d'exécution, erreurs, validations,
    annulations, reprises, automatisations IA déclenchées" (sprint
    requirement)."""

    workflow_id: str
    execution_id: str
    duration_ms: float
    step_count: int
    error_count: int
    validation_count: int
    cancellation_count: int
    retry_count: int
    ai_automations_triggered: int
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
