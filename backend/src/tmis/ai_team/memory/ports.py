from typing import Protocol

from tmis.ai_team.memory.schemas import AgentPreferences, LongTermMemoryEntry, ShortTermMemoryEntry


class AgentMemoryPort(Protocol):
    """Port implemented by every interchangeable agent memory store
    (see docs/53-guide-creation-agent.md — Mémoire). The in-memory
    reference implementation shipped this sprint is process-local and
    non-persistent by design; the port is the seam a future
    database-backed store plugs into without any agent code changing."""

    def remember_short_term(self, agent_id: str, mission_id: str, content: str) -> None: ...

    def recent_short_term(
        self, agent_id: str, *, limit: int = 10
    ) -> list[ShortTermMemoryEntry]: ...

    def remember_long_term(
        self, agent_id: str, summary: str, tags: frozenset[str] = frozenset()
    ) -> None: ...

    def search_long_term(self, agent_id: str, tag: str) -> list[LongTermMemoryEntry]: ...

    def get_preferences(self, agent_id: str) -> AgentPreferences: ...

    def set_preference(self, agent_id: str, key: str, value: str) -> None: ...
