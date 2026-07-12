from typing import Protocol

from tmis.business_platform.quotas.schemas import QuotaDimension, QuotaOverride


class QuotaOverrideStorePort(Protocol):
    def save(self, override: QuotaOverride) -> None: ...

    def get(self, firm_id: str, dimension: QuotaDimension) -> QuotaOverride | None: ...

    def list_for_firm(self, firm_id: str) -> list[QuotaOverride]: ...
