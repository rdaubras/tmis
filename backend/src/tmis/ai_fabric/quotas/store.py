import time

from tmis.ai_fabric.quotas.schemas import Quota


class InMemoryQuotaStore:
    def __init__(self) -> None:
        self._quotas: dict[tuple[str, str], Quota] = {}
        self._calls: dict[tuple[str, str], list[float]] = {}

    def set_quota(self, quota: Quota) -> None:
        self._quotas[(quota.scope, quota.scope_id)] = quota

    def get_quota(self, scope: str, scope_id: str) -> Quota | None:
        return self._quotas.get((scope, scope_id))

    def record_call(self, scope: str, scope_id: str) -> None:
        self._calls.setdefault((scope, scope_id), []).append(time.monotonic())

    def calls_in_period(self, scope: str, scope_id: str, period_days: int) -> int:
        timestamps = self._calls.get((scope, scope_id), [])
        cutoff = time.monotonic() - period_days * 86400
        return sum(1 for t in timestamps if t >= cutoff)
