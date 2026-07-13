from tmis.runtime_platform.runtime_orchestrator.engine import TaskRunner
from tmis.workflow_automation.execution_engine.engine import ExecutionEngine
from tmis.workflow_automation.execution_engine.schemas import WorkflowExecution
from tmis.workflow_automation.workflow_engine.schemas import Workflow


def workflow_execution_task_runner(
    execution_engine: ExecutionEngine,
    execution: WorkflowExecution,
    workflow: Workflow,
    context: dict[str, str],
) -> TaskRunner:
    """Lets a `RuntimeTask` reuse `workflow_automation.execution_engine.
    ExecutionEngine.resume` instead of the orchestrator reimplementing
    step execution — "réutiliser le Workflow Engine lorsque cela est
    pertinent" (sprint requirement). `ExecutionEngine` itself is
    unmodified: this is an adapter, not a migration of its code, so
    every existing caller of `ExecutionEngine` keeps working exactly
    as before."""

    async def _run(_checkpoint: int) -> None:
        await execution_engine.resume(execution, workflow, context)

    return _run
