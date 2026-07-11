from typing import Any

from tmis.platform_sdk.plugin_system.schemas import PluginType
from tmis.platform_sdk.sdk.schemas import PluginContext
from tmis.platform_sdk.workflow_sdk.executor import WorkflowActionRegistry, WorkflowExecutor
from tmis.platform_sdk.workflow_sdk.schemas import WorkflowDefinition


class BaseWorkflowPlugin:
    """Wraps a declarative `WorkflowDefinition` as a `PluginPort` —
    unlike `BaseAgentPlugin`/`BaseConnectorPlugin`, a workflow plugin
    has nothing for its author to subclass: the workflow itself is
    data (steps/conditions/actions), and only the named actions it
    references are real code, registered ahead of time in a
    `WorkflowActionRegistry`."""

    plugin_type = PluginType.WORKFLOW

    def __init__(
        self, plugin_id: str, definition: WorkflowDefinition, actions: WorkflowActionRegistry
    ) -> None:
        self.id = plugin_id
        self.definition = definition
        self._executor = WorkflowExecutor(actions)

    async def invoke(self, context: PluginContext, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self._executor.run(self.definition, context, payload)
        await context.events.publish(
            "TaskCompleted", {"plugin_id": self.id, "success": result.success}
        )
        return {
            "executed_step_ids": list(result.executed_step_ids),
            "final_context": result.final_context,
            "success": result.success,
        }
