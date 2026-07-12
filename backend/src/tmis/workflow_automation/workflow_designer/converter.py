from tmis.workflow_automation.workflow_designer.schemas import (
    DesignerEdge,
    DesignerNode,
    DesignerNodeKind,
    WorkflowGraph,
)
from tmis.workflow_automation.workflow_engine.schemas import Workflow


def workflow_to_graph(workflow: Workflow) -> WorkflowGraph:
    """Renders a `Workflow` as trigger nodes feeding into an ordered
    chain of action nodes (each with an optional condition node
    inline before it), for a future GUI to lay out."""
    nodes: list[DesignerNode] = []
    edges: list[DesignerEdge] = []

    trigger_node_ids: list[str] = []
    for trigger in workflow.triggers:
        node_id = f"trigger-{trigger.id}"
        nodes.append(
            DesignerNode(
                id=node_id,
                kind=DesignerNodeKind.TRIGGER,
                label=trigger.trigger_type.value,
                config=dict(trigger.config),
            )
        )
        trigger_node_ids.append(node_id)

    previous_node_id: str | None = None
    for step in sorted(workflow.steps, key=lambda s: s.order):
        step_node_id = f"step-{step.order}"
        if step.condition is not None:
            condition_node_id = f"condition-{step.order}"
            nodes.append(
                DesignerNode(
                    id=condition_node_id,
                    kind=DesignerNodeKind.CONDITION,
                    label=f"condition({step.name})",
                )
            )
            edges.append(DesignerEdge(from_node_id=condition_node_id, to_node_id=step_node_id))
            gate_node_id = condition_node_id
        else:
            gate_node_id = step_node_id

        nodes.append(
            DesignerNode(
                id=step_node_id,
                kind=DesignerNodeKind.ACTION,
                label=step.name,
                config=dict(step.action.config),
            )
        )

        if previous_node_id is not None:
            edges.append(DesignerEdge(from_node_id=previous_node_id, to_node_id=gate_node_id))
        else:
            for trigger_node_id in trigger_node_ids:
                edges.append(DesignerEdge(from_node_id=trigger_node_id, to_node_id=gate_node_id))
        previous_node_id = step_node_id

    return WorkflowGraph(workflow_id=workflow.id, nodes=tuple(nodes), edges=tuple(edges))
