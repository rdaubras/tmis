from dataclasses import dataclass, field
from enum import Enum


class CaseNodeType(str, Enum):
    ACTOR = "actor"
    DOCUMENT = "document"
    EVENT = "event"
    FACT = "fact"
    EXHIBIT = "exhibit"
    ISSUE = "issue"


@dataclass(frozen=True, slots=True)
class CaseNode:
    id: str
    type: CaseNodeType
    label: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CaseEdge:
    source_id: str
    target_id: str
    relation: str
