from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ShortTermMemoryEntry:
    """One recent interaction kept for an agent within a single
    mission (see docs/53-guide-creation-agent.md — Mémoire). Bounded:
    only the most recent entries are kept, so short-term memory never
    grows unbounded within a long-running mission."""

    agent_id: str
    mission_id: str
    content: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class LongTermMemoryEntry:
    """A durable experience an agent keeps across missions — e.g. "the
    last time I analyzed a commercial lease dispute, X mattered".
    Unbounded, tagged for retrieval."""

    agent_id: str
    summary: str
    tags: frozenset[str] = frozenset()
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class AgentPreferences:
    agent_id: str
    values: dict[str, str] = field(default_factory=dict)
