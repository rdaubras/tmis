from tmis.ai_fabric.benchmark.ports import BenchmarkStorePort
from tmis.ai_fabric.benchmark.schemas import BenchmarkRun
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.token_manager.engine import estimate_tokens

_HALLUCINATION_PENALTY = 0.1
_QUALITY_SCORE_SMOOTHING = 0.3


class BenchmarkEngine:
    """The sprint's "BENCHMARK ENGINE": measures quality, cost,
    latency, hallucinations, stability, and token consumption for a
    model's response, and — per the sprint's explicit requirement
    that "les résultats alimentent automatiquement le routeur" —
    folds the measured quality into the model's registered
    `quality_score` (an exponential moving average) so
    `tmis.ai_fabric.router` benefits without any manual curation."""

    def __init__(
        self,
        store: BenchmarkStorePort,
        model_registry: ModelRegistryPort,
        evaluator: ResponseEvaluator | None = None,
    ) -> None:
        self._store = store
        self._model_registry = model_registry
        self._evaluator = evaluator or ResponseEvaluator()

    def run(
        self, model_name: str, response_text: str, *, cost_usd: float, latency_ms: float
    ) -> BenchmarkRun:
        metrics = self._evaluator.evaluate(response_text)
        hallucination_flags = len(metrics.contradiction_flags)
        quality_score = max(
            0.0, metrics.coherence_score - _HALLUCINATION_PENALTY * hallucination_flags
        )
        run = BenchmarkRun(
            model_name=model_name,
            quality_score=quality_score,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            hallucination_flags=hallucination_flags,
            token_count=estimate_tokens(response_text),
        )
        self._store.record(run)
        self._feed_router(model_name, quality_score)
        return run

    def _feed_router(self, model_name: str, quality_score: float) -> None:
        model = self._model_registry.get(model_name)
        if model is None:
            return
        model.quality_score = (
            1 - _QUALITY_SCORE_SMOOTHING
        ) * model.quality_score + _QUALITY_SCORE_SMOOTHING * quality_score

    def history(self, model_name: str) -> list[BenchmarkRun]:
        return self._store.history(model_name)

    def comparison_table(self) -> list[BenchmarkRun]:
        return sorted(self._store.all_latest(), key=lambda r: r.quality_score, reverse=True)
