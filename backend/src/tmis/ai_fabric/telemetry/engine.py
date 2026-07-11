from tmis.ai_fabric.fallback.engine import FallbackEngine
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.quality_optimizer.engine import QualityOptimizer
from tmis.ai_fabric.telemetry.schemas import FabricTelemetry, ModelTelemetrySnapshot
from tmis.platform.cost_control.engine import CostTrackerEngine


class TelemetryDashboard:
    """Aggregates the sprint's dashboard requirement (coût par
    modèle, qualité, temps moyen, disponibilité, taux d'usage, taux
    de fallback, économies réalisées) — a read-only composition over
    `tmis.ai_fabric.model_registry`, `tmis.ai_fabric.quality_optimizer`,
    `tmis.ai_fabric.fallback`, and `tmis.platform.cost_control`, never
    a new source of truth."""

    def __init__(
        self,
        model_registry: ModelRegistryPort,
        quality_optimizer: QualityOptimizer,
        fallback_engine: FallbackEngine,
        cost_tracker: CostTrackerEngine,
        firm_id: str,
    ) -> None:
        self._model_registry = model_registry
        self._quality_optimizer = quality_optimizer
        self._fallback_engine = fallback_engine
        self._cost_tracker = cost_tracker
        self._firm_id = firm_id

    def snapshot(self) -> FabricTelemetry:
        models = self._model_registry.list_all()
        stats_by_model = {model.name: self._quality_optimizer.stats(model.name) for model in models}
        total_calls = sum(stats.total_calls for stats in stats_by_model.values())

        rows = tuple(
            ModelTelemetrySnapshot(
                model_name=model.name,
                availability=model.availability,
                quality_score=model.quality_score,
                average_latency_ms=model.avg_latency_ms,
                cost_per_1k_tokens_usd=model.cost_per_1k_tokens_usd,
                error_rate=stats_by_model[model.name].error_rate,
                stability_score=stats_by_model[model.name].stability_score,
                average_feedback=stats_by_model[model.name].average_feedback,
                total_calls=stats_by_model[model.name].total_calls,
                usage_share=(
                    stats_by_model[model.name].total_calls / total_calls if total_calls else 0.0
                ),
            )
            for model in models
        )

        return FabricTelemetry(
            models=rows,
            fallback_rate=self._fallback_engine.fallback_rate(),
            cache_hit_rate=self._cost_tracker.cache_hit_rate(self._firm_id),
        )
