from typing import Protocol

from tmis.ai.evaluation.metrics import EvaluationMetrics


class EvaluationSinkPort(Protocol):
    """A destination for recorded metrics (in-memory, logs, a future
    metrics backend such as Prometheus)."""

    def record(self, metrics: EvaluationMetrics) -> None: ...
