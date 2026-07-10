from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    DOCUMENT = "document"
    SECTION = "section"
    ENTITY = "entity"
    DATE = "date"
    EVENT = "event"
    REFERENCE = "reference"
    CHUNK = "chunk"


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    id: str
    type: NodeType
    label: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class KnowledgeEdge:
    source_id: str
    target_id: str
    relation: str
