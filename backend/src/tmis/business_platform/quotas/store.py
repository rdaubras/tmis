from tmis.business_platform.quotas.schemas import QuotaDimension, QuotaOverride


class InMemoryQuotaOverrideStore:
    def __init__(self) -> None:
        self._overrides: dict[tuple[str, QuotaDimension], QuotaOverride] = {}

    def save(self, override: QuotaOverride) -> None:
        self._overrides[(override.firm_id, override.dimension)] = override

    def get(self, firm_id: str, dimension: QuotaDimension) -> QuotaOverride | None:
        return self._overrides.get((firm_id, dimension))

    def list_for_firm(self, firm_id: str) -> list[QuotaOverride]:
        return [o for (fid, _dim), o in self._overrides.items() if fid == firm_id]
