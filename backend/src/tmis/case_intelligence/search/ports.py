from typing import TYPE_CHECKING, Protocol

from tmis.case_intelligence.search.schemas import CaseSearchResult

if TYPE_CHECKING:
    from tmis.case_intelligence.cases.schemas import CaseProfile


class CaseSearchPort(Protocol):
    """Port implemented by every interchangeable case-search engine."""

    async def reindex(self, profile: "CaseProfile") -> None: ...

    async def search(self, query: str, *, top_k: int = 10) -> list[CaseSearchResult]: ...
