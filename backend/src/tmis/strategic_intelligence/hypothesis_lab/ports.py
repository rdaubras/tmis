from typing import Protocol

from tmis.strategic_intelligence.hypothesis_lab.schemas import (
    HypothesisEvent,
    StrategicHypothesis,
)


class HypothesisLabStorePort(Protocol):
    def add(self, firm_id: str, hypothesis: StrategicHypothesis) -> None: ...

    def get(self, firm_id: str, hypothesis_id: str) -> StrategicHypothesis | None: ...

    def list_for_case(self, firm_id: str, case_id: str) -> list[StrategicHypothesis]: ...

    def append_event(self, event: HypothesisEvent) -> None: ...

    def history(self, firm_id: str, hypothesis_id: str) -> list[HypothesisEvent]: ...
