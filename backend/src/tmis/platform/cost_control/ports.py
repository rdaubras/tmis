from typing import Protocol

from tmis.platform.cost_control.schemas import AlertThreshold, CostBreach, CostEntry


class CostEntryStorePort(Protocol):
    def save(self, entry: CostEntry) -> None: ...

    def list_all(self) -> list[CostEntry]: ...

    def list_for_firm(self, firm_id: str) -> list[CostEntry]: ...

    def list_for_user(self, user_id: str) -> list[CostEntry]: ...

    def list_for_case(self, case_id: str) -> list[CostEntry]: ...

    def list_for_workflow(self, workflow_id: str) -> list[CostEntry]: ...


class AlertThresholdStorePort(Protocol):
    def save(self, threshold: AlertThreshold) -> None: ...

    def list_all(self) -> list[AlertThreshold]: ...


class CostTrackerEnginePort(Protocol):
    """Port implemented by every interchangeable cost tracker."""

    def record(
        self,
        firm_id: str,
        user_id: str,
        provider: str,
        model: str,
        token_count: int,
        *,
        case_id: str | None = None,
        workflow_id: str | None = None,
        cache_hit: bool = False,
    ) -> CostEntry: ...

    def cost_by_user(self, user_id: str) -> float: ...

    def cost_by_case(self, case_id: str) -> float: ...

    def cost_by_workflow(self, workflow_id: str) -> float: ...

    def cost_by_provider(self, firm_id: str, provider: str) -> float: ...

    def total_cost_usd(self) -> float: ...

    def cache_hit_rate(self, firm_id: str) -> float: ...

    def set_alert_threshold(
        self, scope: str, scope_id: str, max_cost_usd: float, period_days: int = 30
    ) -> AlertThreshold: ...

    def check_thresholds(self, firm_id: str) -> list[CostBreach]: ...
