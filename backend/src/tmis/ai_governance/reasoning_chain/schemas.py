import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ChainStageType(StrEnum):
    """The sprint's explicit reasoning pipeline: Question → Analyse →
    Recherche → Arguments → Contre-arguments → Consensus → Validation
    → Brouillon. Declaration order doubles as the canonical stage
    order enforced by `ReasoningChainEngine`."""

    QUESTION = "question"
    ANALYSIS = "analyse"
    RESEARCH = "recherche"
    ARGUMENTS = "arguments"
    COUNTER_ARGUMENTS = "contre_arguments"
    CONSENSUS = "consensus"
    VALIDATION = "validation"
    DRAFT = "brouillon"


def new_chain_step_id() -> str:
    return f"step-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class ChainStep:
    """One recorded step of a reasoning chain — always carries a
    human-readable `summary`, never a bare status flag."""

    id: str
    stage: ChainStageType
    summary: str
    references: tuple[str, ...] = field(default_factory=tuple)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class ReasoningChain:
    """The full, ordered, visualizable chain of one AI production —
    "chaque étape doit être visualisable" (sprint requirement)."""

    id: str
    firm_id: str
    production_id: str
    steps: list[ChainStep] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ChainNode:
    id: str
    stage: ChainStageType
    label: str


@dataclass(frozen=True, slots=True)
class ChainEdge:
    source_id: str
    target_id: str


@dataclass(frozen=True, slots=True)
class ReasoningChainGraph:
    """A visualizable graph view of a `ReasoningChain` — one node per
    step, edges linking each step to the next in recorded order."""

    nodes: tuple[ChainNode, ...]
    edges: tuple[ChainEdge, ...]


class OutOfOrderStepError(Exception):
    def __init__(self, from_stage: ChainStageType, to_stage: ChainStageType) -> None:
        super().__init__(
            f"Cannot record stage {to_stage.value!r} after {from_stage.value!r}: "
            "the reasoning chain only moves forward through its canonical stages."
        )
        self.from_stage = from_stage
        self.to_stage = to_stage
