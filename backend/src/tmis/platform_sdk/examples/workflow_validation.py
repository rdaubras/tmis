"""The sprint's "Workflow Validation" example plugin — demonstrates
`tmis.platform_sdk.workflow_sdk`: a declarative, conditional workflow
(approve small amounts automatically, route larger ones to a second
step) plus the small action registry it depends on."""

from typing import Any

from tmis.platform_sdk.sdk.schemas import PluginContext
from tmis.platform_sdk.workflow_sdk.base import BaseWorkflowPlugin
from tmis.platform_sdk.workflow_sdk.executor import WorkflowActionRegistry
from tmis.platform_sdk.workflow_sdk.schemas import (
    ConditionOperator,
    WorkflowCondition,
    WorkflowDefinition,
    WorkflowStep,
)

PLUGIN_ID = "workflow-validation"

_AUTO_APPROVAL_THRESHOLD = 1000

_DEFINITION = WorkflowDefinition(
    id=PLUGIN_ID,
    name="Validation de dépense",
    steps=(
        WorkflowStep(
            id="check-amount",
            name="Vérifier le montant",
            action="check_amount",
            condition=WorkflowCondition(
                "amount", ConditionOperator.LESS_THAN, _AUTO_APPROVAL_THRESHOLD
            ),
            on_success="auto-approve",
            on_failure="request-partner-approval",
        ),
        WorkflowStep(id="auto-approve", name="Approbation automatique", action="approve"),
        WorkflowStep(
            id="request-partner-approval", name="Demander l'aval d'un associé", action="flag"
        ),
    ),
    trigger_events=("TaskCompleted",),
    validations=("amount doit être un nombre positif",),
)


async def _check_amount(context: PluginContext, run_context: dict[str, Any]) -> dict[str, Any]:
    return {}


async def _approve(context: PluginContext, run_context: dict[str, Any]) -> dict[str, Any]:
    return {"decision": "approved_automatically"}


async def _flag(context: PluginContext, run_context: dict[str, Any]) -> dict[str, Any]:
    return {"decision": "requires_partner_approval"}


def build_action_registry() -> WorkflowActionRegistry:
    registry = WorkflowActionRegistry()
    registry.register("check_amount", _check_amount)
    registry.register("approve", _approve)
    registry.register("flag", _flag)
    return registry


class WorkflowValidationPlugin(BaseWorkflowPlugin):
    def __init__(self) -> None:
        super().__init__(
            plugin_id=PLUGIN_ID, definition=_DEFINITION, actions=build_action_registry()
        )
