import pytest

from tmis.workflow_automation.action_engine import (
    ACTION_CREATE_TASK,
    Action,
    ActionEngine,
    ActionResult,
    InMemoryActionLogStore,
    new_action_id,
)
from tmis.workflow_automation.condition_engine import ConditionEngine
from tmis.workflow_automation.condition_engine.schemas import Comparator, cond_compare
from tmis.workflow_automation.execution_engine import (
    ExecutionEngine,
    ExecutionStatus,
    InMemoryExecutionStore,
    WorkflowExecutionError,
)
from tmis.workflow_automation.retry import WorkflowRetryPolicy
from tmis.workflow_automation.rollback import (
    InMemoryRollbackLogStore,
    RollbackEngine,
    RollbackResult,
)
from tmis.workflow_automation.workflow_engine import (
    InMemoryWorkflowStore,
    WorkflowEngine,
    WorkflowStep,
)


class _AlwaysSucceeds:
    action_type = ACTION_CREATE_TASK

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail="ok")


class _AlwaysFails:
    action_type = "always_fails"

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=False, detail="nope")


class _FlakyOnce:
    """Fails its first call, succeeds every call after — one retry
    attempt per `start()`/`resume()`, so a single resume is enough to
    turn a failed execution into a completed one."""

    action_type = "flaky"

    def __init__(self) -> None:
        self.attempts = 0

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        self.attempts += 1
        if self.attempts < 2:
            return ActionResult(success=False, detail="transient")
        return ActionResult(success=True, detail="finally ok")


def _make_execution_engine(handlers: list) -> ExecutionEngine:
    action_engine = ActionEngine(InMemoryActionLogStore(), handlers)
    return ExecutionEngine(
        InMemoryExecutionStore(),
        action_engine,
        ConditionEngine(),
        retry_policy=WorkflowRetryPolicy(max_attempts=3, base_delay_seconds=0.001),
    )


@pytest.mark.asyncio
async def test_execution_engine_runs_sequential_steps_to_completion() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    step1 = WorkflowStep(0, "one", Action(new_action_id(), "wf", ACTION_CREATE_TASK))
    step2 = WorkflowStep(1, "two", Action(new_action_id(), "wf", ACTION_CREATE_TASK))
    workflow = we.create("firm-1", "Test", owner="a", steps=(step1, step2))
    ee = _make_execution_engine([_AlwaysSucceeds()])

    execution = await ee.start(workflow, {})

    assert execution.status is ExecutionStatus.COMPLETED
    assert execution.current_step_index == 2
    assert len(execution.step_results) == 2


@pytest.mark.asyncio
async def test_execution_engine_skips_step_with_false_condition() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    gated_step = WorkflowStep(
        0,
        "gated",
        Action(new_action_id(), "wf", ACTION_CREATE_TASK),
        condition=cond_compare("go", Comparator.EQ, "yes"),
    )
    workflow = we.create("firm-1", "Test", owner="a", steps=(gated_step,))
    ee = _make_execution_engine([_AlwaysSucceeds()])

    execution = await ee.start(workflow, {"go": "no"})

    assert execution.status is ExecutionStatus.COMPLETED
    assert execution.step_results[0].skipped is True


@pytest.mark.asyncio
async def test_execution_engine_workflow_level_condition_cancels() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    workflow = we.create(
        "firm-1", "Test", owner="a", conditions=(cond_compare("ready", Comparator.EQ, "true"),)
    )
    ee = _make_execution_engine([])

    execution = await ee.start(workflow, {"ready": "false"})

    assert execution.status is ExecutionStatus.CANCELLED


@pytest.mark.asyncio
async def test_execution_engine_failing_step_fails_execution_without_advancing() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    step = WorkflowStep(0, "fails", Action(new_action_id(), "wf", "always_fails"))
    workflow = we.create("firm-1", "Test", owner="a", steps=(step,))
    ee = _make_execution_engine([_AlwaysFails()])

    execution = await ee.start(workflow, {})

    assert execution.status is ExecutionStatus.FAILED
    assert execution.current_step_index == 0
    assert execution.failure_reason


@pytest.mark.asyncio
async def test_execution_engine_resume_continues_from_failed_step() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    step1 = WorkflowStep(0, "ok", Action(new_action_id(), "wf", ACTION_CREATE_TASK))
    step2 = WorkflowStep(1, "fails-then-succeeds", Action(new_action_id(), "wf", "flaky"))
    workflow = we.create("firm-1", "Test", owner="a", steps=(step1, step2))
    action_engine = ActionEngine(InMemoryActionLogStore(), [_AlwaysSucceeds(), _FlakyOnce()])
    ee = ExecutionEngine(
        InMemoryExecutionStore(),
        action_engine,
        ConditionEngine(),
        retry_policy=WorkflowRetryPolicy(max_attempts=1),
    )

    execution = await ee.start(workflow, {})
    assert execution.status is ExecutionStatus.FAILED
    assert execution.current_step_index == 1

    resumed = await ee.resume(execution, workflow, {})

    assert resumed.status is ExecutionStatus.COMPLETED
    assert resumed.current_step_index == 2


@pytest.mark.asyncio
async def test_execution_engine_resume_rejects_completed_execution() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    workflow = we.create("firm-1", "Test", owner="a")
    ee = _make_execution_engine([])

    execution = await ee.start(workflow, {})
    assert execution.status is ExecutionStatus.COMPLETED

    with pytest.raises(WorkflowExecutionError):
        await ee.resume(execution, workflow, {})


@pytest.mark.asyncio
async def test_execution_engine_runs_parallel_group_concurrently() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    a = WorkflowStep(0, "a", Action(new_action_id(), "wf", ACTION_CREATE_TASK), parallel_group="g1")
    b = WorkflowStep(1, "b", Action(new_action_id(), "wf", ACTION_CREATE_TASK), parallel_group="g1")
    workflow = we.create("firm-1", "Test", owner="a", steps=(a, b))
    ee = _make_execution_engine([_AlwaysSucceeds()])

    execution = await ee.start(workflow, {})

    assert execution.status is ExecutionStatus.COMPLETED
    assert len(execution.step_results) == 2


def test_retry_policy_retries_until_success() -> None:
    import asyncio

    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("fail")
        return "ok"

    policy = WorkflowRetryPolicy(max_attempts=3, base_delay_seconds=0.001)
    result = asyncio.run(policy.run(flaky))

    assert result == "ok"
    assert attempts["count"] == 2


def test_rollback_engine_journals_every_attempt() -> None:
    engine = RollbackEngine(InMemoryRollbackLogStore())

    class _Handler:
        action_type = ACTION_CREATE_TASK

        def compensate(self, action: Action, context: dict[str, str]) -> RollbackResult:
            return RollbackResult(compensated=True, detail="cancelled")

    engine.register(_Handler())
    action = Action(new_action_id(), "wf", ACTION_CREATE_TASK)

    result = engine.rollback("firm-1", "exec-1", action, {})

    assert result.compensated is True
    assert len(engine.history_for_execution("firm-1", "exec-1")) == 1


def test_rollback_engine_no_handler_reports_not_compensated() -> None:
    engine = RollbackEngine(InMemoryRollbackLogStore())
    action = Action(new_action_id(), "wf", "no_handler")

    result = engine.rollback("firm-1", "exec-1", action, {})

    assert result.compensated is False
