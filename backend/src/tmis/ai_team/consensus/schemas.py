from dataclasses import dataclass, field

from tmis.ai.schemas.agent import ConfidenceLevel


@dataclass(frozen=True, slots=True)
class AgentPosition:
    """One agent's answer to a shared question, submitted for
    consensus-building (see docs/56-guide-consensus-critique.md)."""

    agent_id: str
    text: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


@dataclass(frozen=True, slots=True)
class ConsensusResult:
    topic: str
    positions: tuple[AgentPosition, ...]
    agreement_ratio: float
    consensus_text: str
    disagreements: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_persistent_disagreement(self) -> bool:
        return len(self.disagreements) > 0
