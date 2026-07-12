"""Architecture for a future visual workflow designer — schemas and a
`Workflow -> WorkflowGraph` serializer only. "L'interface graphique
sera développée dans un sprint ultérieur" (sprint requirement); this
module exists so that sprint can render a graph without having to
invent the node/edge shape from scratch."""

from dataclasses import dataclass, field
from enum import StrEnum


class DesignerNodeKind(StrEnum):
    TRIGGER = "trigger"
    CONDITION = "condition"
    ACTION = "action"
    VALIDATION = "validation"
    BRANCH = "branch"


@dataclass(frozen=True, slots=True)
class DesignerNode:
    id: str
    kind: DesignerNodeKind
    label: str
    config: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DesignerEdge:
    from_node_id: str
    to_node_id: str
    label: str = ""


@dataclass(frozen=True, slots=True)
class WorkflowGraph:
    workflow_id: str
    nodes: tuple[DesignerNode, ...] = field(default_factory=tuple)
    edges: tuple[DesignerEdge, ...] = field(default_factory=tuple)
