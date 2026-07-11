from tmis.ai_governance.explainability.ports import ExplainabilityStorePort
from tmis.ai_governance.explainability.schemas import (
    ExplainabilityReport,
    IgnoredElement,
    new_explainability_report_id,
)


class ExplainabilityEngine:
    """The sprint's "EXPLAINABILITY ENGINE": generates, for one AI
    production, a report readable by a lawyer — never a developer-only
    trace. Deliberately takes its inputs pre-assembled rather than
    reaching into `reasoning_chain`/`ai_team`/`ai_fabric` itself; the
    top-level `AIGovernancePlatform` facade is what pulls steps from
    `ReasoningChainEngine`, agents from the mission that produced the
    output, etc., and hands them here."""

    def __init__(self, store: ExplainabilityStorePort) -> None:
        self._store = store

    def generate(
        self,
        firm_id: str,
        production_id: str,
        *,
        summary: str,
        steps_followed: tuple[str, ...],
        agents_involved: tuple[str, ...] = (),
        models_used: tuple[str, ...] = (),
        legal_references: tuple[str, ...] = (),
        documents_consulted: tuple[str, ...] = (),
        ignored_elements: tuple[IgnoredElement, ...] = (),
    ) -> ExplainabilityReport:
        report = ExplainabilityReport(
            id=new_explainability_report_id(),
            firm_id=firm_id,
            production_id=production_id,
            summary=summary,
            steps_followed=steps_followed,
            agents_involved=agents_involved,
            models_used=models_used,
            legal_references=legal_references,
            documents_consulted=documents_consulted,
            ignored_elements=ignored_elements,
        )
        self._store.save(report)
        return report

    def history(self, firm_id: str, production_id: str) -> list[ExplainabilityReport]:
        return self._store.list_for_production(firm_id, production_id)

    def latest(self, firm_id: str, production_id: str) -> ExplainabilityReport | None:
        history = self.history(firm_id, production_id)
        return history[-1] if history else None
