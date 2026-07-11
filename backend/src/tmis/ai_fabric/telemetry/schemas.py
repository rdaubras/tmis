from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelTelemetrySnapshot:
    """One row of the sprint's observability dashboard requirement:
    coût par modèle, qualité, temps moyen, disponibilité, taux
    d'usage, stabilité. `fallback_rate` is Fabric-wide (not
    per-model), attached here for a single, one-call dashboard read."""

    model_name: str
    availability: bool
    quality_score: float
    average_latency_ms: float
    cost_per_1k_tokens_usd: float
    error_rate: float
    stability_score: float
    average_feedback: float
    total_calls: int
    usage_share: float


@dataclass(frozen=True, slots=True)
class FabricTelemetry:
    models: tuple[ModelTelemetrySnapshot, ...]
    fallback_rate: float
    cache_hit_rate: float
