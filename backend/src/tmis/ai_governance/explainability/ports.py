from typing import Protocol

from tmis.ai_governance.explainability.schemas import ExplainabilityReport


class ExplainabilityStorePort(Protocol):
    def save(self, report: ExplainabilityReport) -> None: ...

    def list_for_production(
        self, firm_id: str, production_id: str
    ) -> list[ExplainabilityReport]: ...
