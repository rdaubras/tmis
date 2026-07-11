from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.sdk.schemas import PluginContext
from tmis.platform_sdk.workflow_sdk.base import BaseWorkflowPlugin
from tmis.platform_sdk.workflow_sdk.executor import WorkflowActionRegistry, WorkflowExecutor
from tmis.platform_sdk.workflow_sdk.schemas import (
    ConditionOperator,
    WorkflowCondition,
    WorkflowDefinition,
    WorkflowStep,
    evaluate,
)
from tmis.platform_sdk.workflow_sdk.serialization import from_json, to_json

FIRM = "firm-a"


def _context() -> PluginContext:
    permissions = PermissionEngine(InMemoryPermissionStore())
    return PluginContext(
        firm_id=FIRM,
        actor_id="a",
        plugin_id="wf-1",
        events=PlatformEventBus(),
        permissions=permissions.checker_for(FIRM, "wf-1"),
    )


def test_evaluate_none_condition_is_always_true() -> None:
    assert evaluate(None, {}) is True


def test_evaluate_exists_and_not_exists() -> None:
    condition = WorkflowCondition("amount", ConditionOperator.EXISTS)
    assert evaluate(condition, {"amount": 5}) is True
    assert evaluate(condition, {}) is False


def test_evaluate_equals_and_not_equals() -> None:
    eq = WorkflowCondition("status", ConditionOperator.EQUALS, "ok")
    assert evaluate(eq, {"status": "ok"}) is True
    assert evaluate(eq, {"status": "ko"}) is False

    neq = WorkflowCondition("status", ConditionOperator.NOT_EQUALS, "ok")
    assert evaluate(neq, {"status": "ko"}) is True


def test_evaluate_greater_and_less_than() -> None:
    gt = WorkflowCondition("amount", ConditionOperator.GREATER_THAN, 100)
    assert evaluate(gt, {"amount": 200}) is True
    assert evaluate(gt, {"amount": 50}) is False

    lt = WorkflowCondition("amount", ConditionOperator.LESS_THAN, 100)
    assert evaluate(lt, {"amount": 50}) is True


def test_serialization_roundtrip_preserves_definition() -> None:
    workflow = WorkflowDefinition(
        id="wf-1",
        name="Test",
        steps=(
            WorkflowStep(
                "s1",
                "Step 1",
                "act",
                condition=WorkflowCondition("x", ConditionOperator.EQUALS, 1),
                on_success="s2",
            ),
            WorkflowStep("s2", "Step 2", "act2"),
        ),
        trigger_events=("TaskCompleted",),
        validations=("x must be 1",),
    )

    restored = from_json(to_json(workflow))

    assert restored == workflow


async def test_executor_follows_on_success_branch() -> None:
    registry = WorkflowActionRegistry()

    async def approve(context: PluginContext, run_context: dict) -> dict:  # type: ignore[type-arg]
        return {"approved": True}

    registry.register("approve", approve)
    workflow = WorkflowDefinition(
        id="wf-1",
        name="Simple",
        steps=(WorkflowStep("s1", "Approve", "approve"),),
    )
    executor = WorkflowExecutor(registry)

    result = await executor.run(workflow, _context(), {})

    assert result.success is True
    assert result.final_context == {"approved": True}
    assert result.executed_step_ids == ("s1",)


async def test_executor_takes_failure_edge_when_condition_false() -> None:
    registry = WorkflowActionRegistry()

    async def noop(context: PluginContext, run_context: dict) -> dict:  # type: ignore[type-arg]
        return {}

    registry.register("noop", noop)
    workflow = WorkflowDefinition(
        id="wf-1",
        name="Branch",
        steps=(
            WorkflowStep(
                "s1",
                "Check",
                "noop",
                condition=WorkflowCondition("ready", ConditionOperator.EQUALS, True),
                on_success="s2",
                on_failure="s3",
            ),
            WorkflowStep("s2", "Success path", "noop"),
            WorkflowStep("s3", "Failure path", "noop"),
        ),
    )
    executor = WorkflowExecutor(registry)

    result = await executor.run(workflow, _context(), {"ready": False})

    assert result.executed_step_ids == ("s1", "s3")


async def test_executor_unknown_action_takes_failure_edge() -> None:
    workflow = WorkflowDefinition(
        id="wf-1",
        name="Missing action",
        steps=(WorkflowStep("s1", "Step 1", "does-not-exist"),),
    )
    executor = WorkflowExecutor(WorkflowActionRegistry())

    result = await executor.run(workflow, _context(), {})

    assert result.success is False


async def test_executor_bounds_iterations_on_cyclic_definition() -> None:
    registry = WorkflowActionRegistry()

    async def noop(context: PluginContext, run_context: dict) -> dict:  # type: ignore[type-arg]
        return {}

    registry.register("noop", noop)
    workflow = WorkflowDefinition(
        id="wf-1",
        name="Cycle",
        steps=(
            WorkflowStep("s1", "A", "noop", on_success="s2"),
            WorkflowStep("s2", "B", "noop", on_success="s1"),
        ),
    )
    executor = WorkflowExecutor(registry)

    result = await executor.run(workflow, _context(), {})

    assert len(result.executed_step_ids) == 4


async def test_base_workflow_plugin_invoke_publishes_task_completed() -> None:
    events = PlatformEventBus()
    context = PluginContext(
        firm_id=FIRM,
        actor_id="a",
        plugin_id="wf-1",
        events=events,
        permissions=PermissionEngine(InMemoryPermissionStore()).checker_for(FIRM, "wf-1"),
    )
    registry = WorkflowActionRegistry()

    async def approve(context: PluginContext, run_context: dict) -> dict:  # type: ignore[type-arg]
        return {}

    registry.register("approve", approve)
    plugin = BaseWorkflowPlugin(
        "wf-1",
        WorkflowDefinition(id="wf-1", name="T", steps=(WorkflowStep("s1", "S", "approve"),)),
        registry,
    )

    result = await plugin.invoke(context, {})

    assert result["success"] is True
    assert events.history[0].event_name == "TaskCompleted"
