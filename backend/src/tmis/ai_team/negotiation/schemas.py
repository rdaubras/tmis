from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class NegotiationRound:
    """One agent's recorded position during a negotiation round (see
    docs/56-guide-consensus-critique.md — Negotiation). Append-only."""

    round_number: int
    agent_id: str
    position_text: str
    rationale: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class NegotiationOutcome:
    topic: str
    rounds: tuple[NegotiationRound, ...]
    resolved: bool
    note: str
