from tmis.ai_governance.explainability.schemas import ExplainabilityReport


class InMemoryExplainabilityStore:
    def __init__(self) -> None:
        self._reports: dict[tuple[str, str], list[ExplainabilityReport]] = {}

    def save(self, report: ExplainabilityReport) -> None:
        self._reports.setdefault((report.firm_id, report.production_id), []).append(report)

    def list_for_production(self, firm_id: str, production_id: str) -> list[ExplainabilityReport]:
        return list(self._reports.get((firm_id, production_id), []))
