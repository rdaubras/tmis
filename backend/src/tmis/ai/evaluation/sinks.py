import structlog

from tmis.ai.evaluation.metrics import EvaluationMetrics

logger = structlog.get_logger("tmis.ai.evaluation")


class InMemoryEvaluationSink:
    """Keeps every recorded metric in memory — used in tests and as a
    lightweight default; swap in a real metrics backend in production."""

    def __init__(self) -> None:
        self._metrics: list[EvaluationMetrics] = []

    def record(self, metrics: EvaluationMetrics) -> None:
        self._metrics.append(metrics)

    @property
    def metrics(self) -> list[EvaluationMetrics]:
        return list(self._metrics)


class LoggingEvaluationSink:
    """Emits a structured log line per metric — the extension point future
    sprints can wire to Prometheus/OpenTelemetry (see
    docs/03-architecture-technique.md)."""

    def record(self, metrics: EvaluationMetrics) -> None:
        logger.info(
            "ai_evaluation_metrics",
            provider=metrics.provider,
            model=metrics.model,
            latency_ms=metrics.latency_ms,
            token_count=metrics.token_count,
            estimated_cost_usd=metrics.estimated_cost_usd,
            confidence_score=metrics.confidence_score,
        )
