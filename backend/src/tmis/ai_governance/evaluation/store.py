from tmis.ai_governance.evaluation.schemas import GovernanceRunMetrics


class InMemoryGovernanceMetricsSink:
    def __init__(self) -> None:
        self._metrics: list[GovernanceRunMetrics] = []

    def record(self, metrics: GovernanceRunMetrics) -> None:
        self._metrics.append(metrics)

    def all(self) -> list[GovernanceRunMetrics]:
        return list(self._metrics)
