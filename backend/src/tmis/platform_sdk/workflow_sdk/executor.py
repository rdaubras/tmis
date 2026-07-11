from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from tmis.platform_sdk.sdk.schemas import PluginContext
from tmis.platform_sdk.workflow_sdk.schemas import WorkflowDefinition, WorkflowStep, evaluate

ActionHandler = Callable[[PluginContext, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class WorkflowRunResult:
    executed_step_ids: tuple[str, ...]
    final_context: dict[str, Any]
    success: bool


class UnknownActionError(KeyError):
    pass


class WorkflowActionRegistry:
    """The closed set of actions a workflow may invoke — resolved by
    name from this registry, never by evaluating plugin-authored code
    (same safety rule as `tmis.platform_sdk.plugin_loader`)."""

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, action: str, handler: ActionHandler) -> None:
        self._handlers[action] = handler

    def get(self, action: str) -> ActionHandler | None:
        return self._handlers.get(action)


class WorkflowExecutor:
    """Walks a `WorkflowDefinition` — the sprint's "actions" spec item
    — starting at its first step, following `on_success`/`on_failure`
    edges. A step whose condition doesn't hold, or whose action is
    unregistered or raises, takes the `on_failure` edge; the run stops
    when a step has no outgoing edge for the branch taken. Bounded by
    `len(steps) * 2` iterations so an accidental cycle in a hand-
    written workflow definition can never hang the caller."""

    def __init__(self, actions: WorkflowActionRegistry) -> None:
        self._actions = actions

    async def run(
        self,
        workflow: WorkflowDefinition,
        context: PluginContext,
        initial_context: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        if not workflow.steps:
            return WorkflowRunResult(executed_step_ids=(), final_context={}, success=True)

        steps_by_id = {step.id: step for step in workflow.steps}
        run_context = dict(initial_context or {})
        executed: list[str] = []
        current: WorkflowStep | None = workflow.steps[0]
        max_iterations = len(workflow.steps) * 2
        overall_success = True

        while current is not None and len(executed) < max_iterations:
            executed.append(current.id)
            step_succeeded = evaluate(current.condition, run_context)
            if step_succeeded:
                handler = self._actions.get(current.action)
                if handler is None:
                    step_succeeded = False
                else:
                    try:
                        run_context.update(await handler(context, run_context))
                    except Exception:  # noqa: BLE001 — a failing action takes the failure edge
                        step_succeeded = False

            overall_success = overall_success and step_succeeded
            next_id = current.on_success if step_succeeded else current.on_failure
            current = steps_by_id.get(next_id) if next_id else None

        return WorkflowRunResult(
            executed_step_ids=tuple(executed), final_context=run_context, success=overall_success
        )
