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

        if not all(self._condition_engine.evaluate(c, context) for c in workflow.conditions):
            execution.status = ExecutionStatus.CANCELLED
            execution.failure_reason = "Workflow-level conditions not satisfied"
            execution.completed_at = datetime.now(UTC)
            return execution

        await self._run_from(execution, workflow, context)
        return execution

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
