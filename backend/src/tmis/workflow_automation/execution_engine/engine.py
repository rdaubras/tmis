import asyncio
from datetime import UTC, datetime

from tmis.workflow_automation.action_engine.engine import ActionEngine
from tmis.workflow_automation.action_engine.schemas import ActionResult
from tmis.workflow_automation.condition_engine.engine import ConditionEngine
from tmis.workflow_automation.execution_engine.ports import ExecutionStorePort
from tmis.workflow_automation.execution_engine.schemas import (
    ExecutionStatus,
    StepExecutionResult,
    WorkflowExecution,
    new_execution_id,
)
from tmis.workflow_automation.retry.engine import WorkflowRetryPolicy
from tmis.workflow_automation.workflow_engine.schemas import Workflow, WorkflowStep


class WorkflowExecutionError(Exception):
    pass


class ExecutionEngine:
    """Runs a `Workflow`'s steps sequentially, except consecutive
    steps sharing the same non-null `parallel_group`, which run
    concurrently via `asyncio.gather`. Each step's action goes through
    `WorkflowRetryPolicy` and a per-step timeout; a step that still
    fails after retries raises, which fails the whole execution
    without advancing `current_step_index` — `resume()` then re-runs
    from exactly that step (or that step's parallel group)."""

    def __init__(
        self,
        store: ExecutionStorePort,
        action_engine: ActionEngine,
        condition_engine: ConditionEngine,
        retry_policy: WorkflowRetryPolicy | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._store = store
        self._action_engine = action_engine
        self._condition_engine = condition_engine
        self._retry_policy = retry_policy or WorkflowRetryPolicy()
        self._timeout_seconds = timeout_seconds

    async def start(self, workflow: Workflow, context: dict[str, str]) -> WorkflowExecution:
        execution = WorkflowExecution(
            id=new_execution_id(),
            firm_id=workflow.firm_id,
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self._store.add(execution)
        self._record_started(execution, workflow, context)

        if not all(self._condition_engine.evaluate(c, context) for c in workflow.conditions):
            execution.status = ExecutionStatus.CANCELLED
            execution.failure_reason = "Workflow-level conditions not satisfied"
            execution.completed_at = datetime.now(UTC)
            return execution

        await self._run_from(execution, workflow, context)
        return execution

    def _record_started(
        self, execution: WorkflowExecution, workflow: Workflow, context: dict[str, str]
    ) -> None:
        """Publishes the "Workflow" hop of the sprint's end-to-end
        request trace (Utilisateur → API → Workflow → AI Fabric →
        ...): a `WORKFLOW_COUNT` metric plus a span under the caller's
        `trace_id` (propagated in `context`, per `core.observability.
        trace_id_middleware`) when the workflow was started from an
        HTTP request, so this execution shows up as one hop in that
        request's trace rather than a disconnected event. A local
        import avoids a hard dependency from `workflow_automation` on
        `cloud_operations` at module-import time."""
        from tmis.cloud_operations.bootstrap import get_metrics_engine, get_tracing_engine
        from tmis.cloud_operations.metrics.schemas import MetricCategory
        from tmis.cloud_operations.tracing.schemas import SpanKind

        get_metrics_engine().record(
            MetricCategory.WORKFLOW_COUNT,
            workflow.name,
            1.0,
            firm_id=execution.firm_id,
        )
        trace_id = context.get("trace_id")
        if trace_id is not None:
            span = get_tracing_engine().start_span(
                trace_id,
                SpanKind.WORKFLOW,
                workflow.name,
                firm_id=execution.firm_id,
                attributes={"execution_id": execution.id, "workflow_id": workflow.id},
            )
            execution.telemetry_span_id = span.id

    def get(self, firm_id: str, execution_id: str) -> WorkflowExecution:
        execution = self._store.get(firm_id, execution_id)
        if execution is None:
            raise KeyError(execution_id)
        return execution

    async def resume(
        self, execution: WorkflowExecution, workflow: Workflow, context: dict[str, str]
    ) -> WorkflowExecution:
        if execution.status not in (ExecutionStatus.FAILED, ExecutionStatus.PAUSED):
            raise WorkflowExecutionError(f"Cannot resume execution in status {execution.status}")
        execution.status = ExecutionStatus.RUNNING
        execution.failure_reason = None
        await self._run_from(execution, workflow, context)
        return execution

    async def _run_from(
        self, execution: WorkflowExecution, workflow: Workflow, context: dict[str, str]
    ) -> None:
        ordered_steps = sorted(workflow.steps, key=lambda s: s.order)
        remaining = ordered_steps[execution.current_step_index :]

        try:
            i = 0
            while i < len(remaining):
                step = remaining[i]
                if step.parallel_group is not None:
                    group = [step]
                    i += 1
                    while i < len(remaining) and remaining[i].parallel_group == step.parallel_group:
                        group.append(remaining[i])
                        i += 1
                    results = await asyncio.gather(
                        *(self._run_step(execution, s, context) for s in group)
                    )
                    execution.step_results.extend(results)
                    execution.current_step_index += len(group)
                else:
                    result = await self._run_step(execution, step, context)
                    execution.step_results.append(result)
                    execution.current_step_index += 1
                    i += 1
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(UTC)
        except Exception as exc:
            execution.status = ExecutionStatus.FAILED
            execution.failure_reason = str(exc)
            execution.completed_at = datetime.now(UTC)
            self._record_failure(execution, exc)
        finally:
            self._close_span(execution)
            self._record_workflow_metrics(execution)

    def _close_span(self, execution: WorkflowExecution) -> None:
        if execution.telemetry_span_id is None:
            return
        from tmis.cloud_operations.bootstrap import get_tracing_engine
        from tmis.cloud_operations.tracing.schemas import SpanStatus

        status = SpanStatus.ERROR if execution.status is ExecutionStatus.FAILED else SpanStatus.OK
        get_tracing_engine().end_span(execution.telemetry_span_id, status=status)

    def _record_workflow_metrics(self, execution: WorkflowExecution) -> None:
        """Feeds `workflow_automation.metrics.WorkflowMetricsEngine`
        (Sprint 17), which `cloud_operations.workflow_monitoring`
        (Sprint 22) reads — that sink previously had no caller
        anywhere in the codebase, confirmed by direct search. `retry_
        count`/`ai_automations_triggered`/`validation_count` are
        genuinely not tracked at this granularity today (no per-step
        retry-attempt counter, no validation gateway wired into this
        engine, no AI-step marker) and are reported as `0` rather than
        approximated — a documented gap, not a silent guess."""
        from tmis.workflow_automation.bootstrap import get_workflow_metrics_engine
        from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics

        started_at = execution.started_at or execution.completed_at
        duration_ms = (
            (execution.completed_at - started_at).total_seconds() * 1000
            if started_at is not None and execution.completed_at is not None
            else 0.0
        )
        get_workflow_metrics_engine().record(
            WorkflowRunMetrics(
                workflow_id=execution.workflow_id,
                execution_id=execution.id,
                duration_ms=duration_ms,
                step_count=len(execution.step_results),
                error_count=1 if execution.status is ExecutionStatus.FAILED else 0,
                validation_count=0,
                cancellation_count=1 if execution.status is ExecutionStatus.CANCELLED else 0,
                retry_count=0,
                ai_automations_triggered=0,
            )
        )

    def _record_failure(self, execution: WorkflowExecution, exc: Exception) -> None:
        from tmis.cloud_operations.bootstrap import get_error_tracking_engine

        get_error_tracking_engine().record(
            "workflow_automation",
            type(exc).__name__,
            str(exc),
            firm_id=execution.firm_id,
        )

    async def _run_step(
        self, execution: WorkflowExecution, step: WorkflowStep, context: dict[str, str]
    ) -> StepExecutionResult:
        if step.condition is not None and not self._condition_engine.evaluate(
            step.condition, context
        ):
            return StepExecutionResult(step_order=step.order, skipped=True)

        async def _execute() -> ActionResult:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._action_engine.execute,
                    execution.firm_id,
                    execution.id,
                    step.action,
                    context,
                ),
                timeout=self._timeout_seconds,
            )
            if not result.success:
                raise WorkflowExecutionError(result.detail)
            return result

        action_result = await self._retry_policy.run(_execute)
        return StepExecutionResult(
            step_order=step.order, skipped=False, action_result=action_result
        )
