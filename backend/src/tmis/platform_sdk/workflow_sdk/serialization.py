import json
from typing import Any

from tmis.platform_sdk.workflow_sdk.schemas import (
    ConditionOperator,
    WorkflowCondition,
    WorkflowDefinition,
    WorkflowStep,
)


def to_dict(workflow: WorkflowDefinition) -> dict[str, Any]:
    return {
        "id": workflow.id,
        "name": workflow.name,
        "trigger_events": list(workflow.trigger_events),
        "validations": list(workflow.validations),
        "steps": [
            {
                "id": step.id,
                "name": step.name,
                "action": step.action,
                "condition": (
                    {
                        "field": step.condition.field,
                        "operator": step.condition.operator.value,
                        "value": step.condition.value,
                    }
                    if step.condition is not None
                    else None
                ),
                "on_success": step.on_success,
                "on_failure": step.on_failure,
            }
            for step in workflow.steps
        ],
    }


def from_dict(data: dict[str, Any]) -> WorkflowDefinition:
    steps = tuple(
        WorkflowStep(
            id=s["id"],
            name=s["name"],
            action=s["action"],
            condition=(
                WorkflowCondition(
                    field=s["condition"]["field"],
                    operator=ConditionOperator(s["condition"]["operator"]),
                    value=s["condition"].get("value"),
                )
                if s.get("condition") is not None
                else None
            ),
            on_success=s.get("on_success"),
            on_failure=s.get("on_failure"),
        )
        for s in data["steps"]
    )
    return WorkflowDefinition(
        id=data["id"],
        name=data["name"],
        steps=steps,
        trigger_events=tuple(data.get("trigger_events", ())),
        validations=tuple(data.get("validations", ())),
    )


def to_json(workflow: WorkflowDefinition) -> str:
    return json.dumps(to_dict(workflow), ensure_ascii=False, indent=2)


def from_json(payload: str) -> WorkflowDefinition:
    return from_dict(json.loads(payload))
