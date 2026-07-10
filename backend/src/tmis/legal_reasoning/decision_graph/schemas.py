from dataclasses import dataclass
from enum import Enum


class DecisionNodeType(str, Enum):
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    ARGUMENT = "argument"
    COUNTER_ARGUMENT = "counter_argument"
    EVIDENCE = "evidence"
    REFERENCE = "reference"
    SYNTHESIS = "synthesis"


@dataclass(frozen=True, slots=True)
class DecisionNode:
    id: str
    type: DecisionNodeType
    label: str


@dataclass(frozen=True, slots=True)
class DecisionEdge:
    source_id: str
    target_id: str
    relation: str


@dataclass(frozen=True, slots=True)
class DecisionGraph:
    """A graph exploitable later by the UI (see
    docs/25-legal-reasoning.md — Decision Graph), following the chain
    Question -> Hypotheses -> Arguments -> Counter-arguments -> Evidence
    -> References -> Synthesis."""

    nodes: tuple[DecisionNode, ...]
    edges: tuple[DecisionEdge, ...]
