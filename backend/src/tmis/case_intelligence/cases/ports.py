from typing import Protocol

from tmis.case_intelligence.cases.schemas import CaseProfile


class CaseStorePort(Protocol):
    """Port implemented by every interchangeable `CaseProfile` store."""

    def get(self, case_id: str) -> CaseProfile | None: ...

    def save(self, profile: CaseProfile) -> None: ...

    def get_or_create(self, case_id: str, title: str) -> CaseProfile: ...

    def list_ids(self) -> list[str]: ...
