from typing import Protocol

from tmis.ai_governance.decision_records.schemas import DecisionRecord


class DecisionRecordStorePort(Protocol):
    def add(self, record: DecisionRecord) -> None: ...

    def list_for_production(self, firm_id: str, production_id: str) -> list[DecisionRecord]: ...
