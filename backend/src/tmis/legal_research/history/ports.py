from typing import Protocol

from tmis.legal_research.history.schemas import ResearchHistoryEntry


class ResearchHistoryPort(Protocol):
    """Port implemented by every interchangeable research history store."""

    def record(self, entry: ResearchHistoryEntry) -> None: ...

    def list_for_user(self, user_id: str) -> list[ResearchHistoryEntry]: ...

    def list_for_case(self, case_id: str) -> list[ResearchHistoryEntry]: ...

    def list_all(self) -> list[ResearchHistoryEntry]: ...
