from typing import Protocol

from tmis.strategic_intelligence.learning.schemas import LearningRecord


class LearningStorePort(Protocol):
    def save(self, record: LearningRecord) -> None: ...

    def list_for_case(self, firm_id: str, case_id: str) -> list[LearningRecord]: ...

    def list_for_firm(self, firm_id: str) -> list[LearningRecord]: ...
