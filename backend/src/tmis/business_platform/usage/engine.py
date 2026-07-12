from tmis.business_platform.metering.engine import MeteringEngine
from tmis.business_platform.metering.schemas import MeteredDimension
from tmis.business_platform.quotas.engine import BusinessQuotaEngine
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.business_platform.usage.schemas import UsageSnapshot

_QUOTA_MAPPING: dict[MeteredDimension, QuotaDimension] = {
    MeteredDimension.AI_CALLS: QuotaDimension.AI_CALLS,
    MeteredDimension.STORAGE_GB: QuotaDimension.STORAGE_GB,
    MeteredDimension.WORKFLOWS_EXECUTED: QuotaDimension.WORKFLOWS,
}


class UsageEngine:
    """The usage-vs-quota view for a firm — composes `metering.
    MeteringEngine` (what was consumed) and `quotas.
    BusinessQuotaEngine` (what is allowed), never reimplementing
    either. Not every metered dimension has a quota counterpart (see
    `_QUOTA_MAPPING`) — those still report consumption, just without
    a limit/percentage."""

    def __init__(self, metering: MeteringEngine, quotas: BusinessQuotaEngine) -> None:
        self._metering = metering
        self._quotas = quotas

    def snapshot(self, firm_id: str, dimension: MeteredDimension) -> UsageSnapshot:
        used = self._metering.total_for_dimension(firm_id, dimension)
        quota_dimension = _QUOTA_MAPPING.get(dimension)
        limit = self._quotas.limit_for(firm_id, quota_dimension) if quota_dimension else None
        percent_used = (used / limit * 100) if limit else None
        return UsageSnapshot(
            firm_id=firm_id, dimension=dimension, used=used, limit=limit, percent_used=percent_used
        )

    def full_snapshot(self, firm_id: str) -> list[UsageSnapshot]:
        return [self.snapshot(firm_id, dimension) for dimension in MeteredDimension]
