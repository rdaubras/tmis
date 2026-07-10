from tmis.legal_research.history.schemas import ResearchHistoryEntry


class InMemoryResearchHistory:
    """Implements `ResearchHistoryPort` with an in-memory list — the
    default deployment for Sprint 5; a persisted implementation lands
    with the `document`/`case` bounded contexts (Sprint 7)."""

    def __init__(self) -> None:
        self._entries: list[ResearchHistoryEntry] = []

    def record(self, entry: ResearchHistoryEntry) -> None:
        self._entries.append(entry)

    def list_for_user(self, user_id: str) -> list[ResearchHistoryEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    def list_for_case(self, case_id: str) -> list[ResearchHistoryEntry]:
        return [e for e in self._entries if e.case_id == case_id]

    def list_all(self) -> list[ResearchHistoryEntry]:
        return list(self._entries)
