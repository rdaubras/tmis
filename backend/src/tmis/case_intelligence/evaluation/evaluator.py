from tmis.case_intelligence.evaluation.metrics import CaseUpdateMetrics


class CaseEvaluator:
    """Collects `CaseUpdateMetrics` for every living-case update.

    Mirrors `tmis.document_intelligence.evaluation.PipelineEvaluator`
    (same shape, different concern), so both can later feed the same
    dashboards (see docs/09-roadmap-30-sprints.md).
    """

    def __init__(self) -> None:
        self._history: list[CaseUpdateMetrics] = []

    def record(self, metrics: CaseUpdateMetrics) -> None:
        self._history.append(metrics)

    @property
    def history(self) -> list[CaseUpdateMetrics]:
        return list(self._history)

    def for_case(self, case_id: str) -> list[CaseUpdateMetrics]:
        return [m for m in self._history if m.case_id == case_id]
