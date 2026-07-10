from tmis.document_intelligence.evaluation.metrics import PipelineMetrics


class PipelineEvaluator:
    """Collects `PipelineMetrics` for every pipeline run.

    Kept independent from `tmis.ai.evaluation` (a different concern: AI
    Kernel call metrics vs. document pipeline stage metrics), but follows
    the same shape so both can later feed the same dashboards (see
    docs/09-roadmap-30-sprints.md).
    """

    def __init__(self) -> None:
        self._history: list[PipelineMetrics] = []

    def record(self, metrics: PipelineMetrics) -> None:
        self._history.append(metrics)

    @property
    def history(self) -> list[PipelineMetrics]:
        return list(self._history)

    def for_document(self, document_id: str) -> list[PipelineMetrics]:
        return [m for m in self._history if m.document_id == document_id]
