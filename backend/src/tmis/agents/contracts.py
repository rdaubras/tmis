import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from tmis.domain.shared.ports import Citation


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentInput:
    """Common input contract for every specialized agent (see docs/05)."""

    task_id: uuid.UUID
    case_id: uuid.UUID | None
    context: dict[str, object] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Common output contract for every specialized agent (see docs/05).

    `citations` and `warnings` are never omitted silently: any uncertainty
    or unverifiable claim must surface here rather than in free text.
    """

    result: dict[str, object]
    citations: list[Citation] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    warnings: list[str] = field(default_factory=list)


class AgentPort(Protocol):
    """Every specialized agent node in the orchestration graph implements this."""

    name: str

    async def run(self, agent_input: AgentInput) -> AgentOutput: ...
