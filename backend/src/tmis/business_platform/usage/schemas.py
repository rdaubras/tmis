from dataclasses import dataclass

from tmis.business_platform.metering.schemas import MeteredDimension


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    """One metered dimension's current consumption against its quota
    (when that dimension has one — see `usage.engine._QUOTA_MAPPING`).
    `limit`/`percent_used` are `None` for dimensions metering tracks
    but quotas do not gate (e.g. `TOKENS`, `SEARCHES`)."""

    firm_id: str
    dimension: MeteredDimension
    used: float
    limit: int | None
    percent_used: float | None
