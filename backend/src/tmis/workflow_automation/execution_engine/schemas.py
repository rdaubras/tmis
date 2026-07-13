import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from tmis.workflow_automation.action_engine.schemas import ActionResult


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def new_execution_id() -> str:
    return f"exec-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class StepExecutionResult:
    step_order: int
    skipped: bool
    action_result: ActionResult | None = None


@dataclass(slots=True)
class WorkflowExecution:
    """One run of one workflow version. `current_step_index` is the
    index (into `Workflow.steps`, sorted by `order`) of the next step
    to run — "reprise après interruption" (sprint requirement) means
    `resume()` continues from here rather than restarting."""

    id: str
    firm_id: str
    workflow_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_step_index: int = 0
    step_results: list[StepExecutionResult] = field(default_factory=list)
    failure_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    telemetry_span_id: str | None = None
    """Set by `ExecutionEngine._record_started` when this execution was
    started under an HTTP request's `trace_id` — lets `_run_from` close
    the matching `cloud_operations.tracing` span on completion/failure
    without a second lookup."""
