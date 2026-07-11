from typing import Protocol

from tmis.ai_governance.evaluation.schemas import GovernanceRunMetrics


class GovernanceMetricsSinkPort(Protocol):
    def record(self, metrics: GovernanceRunMetrics) -> None: ...
