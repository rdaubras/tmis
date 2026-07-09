from tmis.ai.evaluation.metrics import EvaluationMetrics
from tmis.ai.evaluation.ports import EvaluationSinkPort
from tmis.ai.evaluation.sinks import InMemoryEvaluationSink


class Evaluator:
    """Fans out every recorded `EvaluationMetrics` to all configured sinks.

    Extensible by design: adding a new metric destination (e.g. a
    Prometheus exporter) means adding a sink, not touching `TMISKernel`.
    """

    def __init__(self, sinks: list[EvaluationSinkPort] | None = None) -> None:
        self._default_sink = InMemoryEvaluationSink()
        self._sinks: list[EvaluationSinkPort] = sinks or [self._default_sink]

    def record(self, metrics: EvaluationMetrics) -> None:
        for sink in self._sinks:
            sink.record(metrics)

    @property
    def in_memory_metrics(self) -> list[EvaluationMetrics]:
        """Convenience accessor for tests; only reflects the default sink."""
        return self._default_sink.metrics
