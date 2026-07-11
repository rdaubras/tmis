from tmis.ai_fabric.quality_optimizer.ports import QualityStatsStorePort
from tmis.ai_fabric.quality_optimizer.schemas import ModelQualityStats


class QualityOptimizer:
    """The sprint's "QUALITY OPTIMIZER": tracks each model's error
    rate, perceived quality, user feedback, and stability over time —
    the router (`tmis.ai_fabric.router`) consults `stability_score`
    and `average_feedback` alongside `ModelDescriptor.quality_score`
    when explaining a routing decision."""

    def __init__(self, store: QualityStatsStorePort) -> None:
        self._store = store

    def record_call(self, model_name: str, *, success: bool) -> None:
        stats = self._store.get_or_create(model_name)
        stats.total_calls += 1
        if not success:
            stats.error_count += 1

    def record_feedback(self, model_name: str, score: float) -> None:
        stats = self._store.get_or_create(model_name)
        stats.feedback_scores.append(score)

    def stats(self, model_name: str) -> ModelQualityStats:
        return self._store.get_or_create(model_name)

    def leaderboard(self) -> list[ModelQualityStats]:
        return sorted(
            self._store.list_all(),
            key=lambda s: (s.stability_score, s.average_feedback),
            reverse=True,
        )
