from collections import defaultdict, deque

from tmis.ai_team.memory.schemas import AgentPreferences, LongTermMemoryEntry, ShortTermMemoryEntry

_SHORT_TERM_MAX_ENTRIES = 20


class InMemoryAgentMemoryStore:
    """Implements `AgentMemoryPort` (see docs/53-guide-creation-agent.md
    — Mémoire). Short-term memory is a bounded per-agent deque (oldest
    entries drop off); long-term memory and preferences are unbounded
    dicts. Process-local only — see the port docstring for the
    persistence roadmap."""

    def __init__(self) -> None:
        self._short_term: dict[str, deque[ShortTermMemoryEntry]] = defaultdict(
            lambda: deque(maxlen=_SHORT_TERM_MAX_ENTRIES)
        )
        self._long_term: dict[str, list[LongTermMemoryEntry]] = defaultdict(list)
        self._preferences: dict[str, AgentPreferences] = {}

    def remember_short_term(self, agent_id: str, mission_id: str, content: str) -> None:
        self._short_term[agent_id].append(
            ShortTermMemoryEntry(agent_id=agent_id, mission_id=mission_id, content=content)
        )

    def recent_short_term(self, agent_id: str, *, limit: int = 10) -> list[ShortTermMemoryEntry]:
        entries = list(self._short_term.get(agent_id, ()))
        return entries[-limit:]

    def remember_long_term(
        self, agent_id: str, summary: str, tags: frozenset[str] = frozenset()
    ) -> None:
        self._long_term[agent_id].append(
            LongTermMemoryEntry(agent_id=agent_id, summary=summary, tags=tags)
        )

    def search_long_term(self, agent_id: str, tag: str) -> list[LongTermMemoryEntry]:
        return [entry for entry in self._long_term.get(agent_id, ()) if tag in entry.tags]

    def get_preferences(self, agent_id: str) -> AgentPreferences:
        return self._preferences.setdefault(agent_id, AgentPreferences(agent_id=agent_id))

    def set_preference(self, agent_id: str, key: str, value: str) -> None:
        self.get_preferences(agent_id).values[key] = value
