from tmis.ai_fabric.quotas.ports import QuotaStorePort
from tmis.ai_fabric.quotas.schemas import Quota


class QuotaEngine:
    """A hard gate on AI Fabric usage — distinct from
    `tmis.platform.cost_control.CostTrackerEngine.check_thresholds`
    (Sprint 10), which only *alerts* on cost overruns. A quota blocks
    the call outright before the Fabric ever routes it."""

    def __init__(self, store: QuotaStorePort) -> None:
        self._store = store

    def set_quota(
        self, scope: str, scope_id: str, max_calls_per_period: int, period_days: int
    ) -> Quota:
        quota = Quota(scope, scope_id, max_calls_per_period, period_days)
        self._store.set_quota(quota)
        return quota

    def check(self, scope: str, scope_id: str) -> bool:
        quota = self._store.get_quota(scope, scope_id)
        if quota is None:
            return True
        return self._store.calls_in_period(scope, scope_id, quota.period_days) < (
            quota.max_calls_per_period
        )

    def record_call(self, scope: str, scope_id: str) -> None:
        self._store.record_call(scope, scope_id)
