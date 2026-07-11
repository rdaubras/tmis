from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.agents.schemas import AgentRole


@dataclass(frozen=True, slots=True)
class ContextSlice:
    """The subset of mission context handed to one agent (see
    docs/56-guide-consensus-critique.md — Context Engine). Never the
    full mission context: only the keys relevant to `role`."""

    agent_role: AgentRole
    content: dict[str, object]
    token_estimate: int


@dataclass(frozen=True, slots=True)
class ContextTraceEntry:
    """One record of "who received what" — the traceability the
    sprint requires. Append-only, never edited or removed."""

    mission_id: str
    agent_role: AgentRole
    keys_included: tuple[str, ...]
    token_estimate: int
    provided_at: datetime = field(default_factory=lambda: datetime.now(UTC))
