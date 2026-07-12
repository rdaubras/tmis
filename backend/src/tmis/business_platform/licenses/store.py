from tmis.business_platform.licenses.schemas import FloatingLicensePool, LicenseGrant


class InMemoryLicenseGrantStore:
    def __init__(self) -> None:
        self._grants: dict[tuple[str, str], LicenseGrant] = {}

    def save(self, grant: LicenseGrant) -> None:
        self._grants[(grant.firm_id, grant.id)] = grant

    def get(self, firm_id: str, grant_id: str) -> LicenseGrant | None:
        return self._grants.get((firm_id, grant_id))

    def list_for_firm(self, firm_id: str) -> list[LicenseGrant]:
        return [g for g in self._grants.values() if g.firm_id == firm_id]

    def list_for_holder(self, firm_id: str, holder_id: str) -> list[LicenseGrant]:
        return [
            g for g in self._grants.values() if g.firm_id == firm_id and g.holder_id == holder_id
        ]


class InMemoryFloatingPoolStore:
    def __init__(self) -> None:
        self._pools: dict[str, FloatingLicensePool] = {}

    def save(self, pool: FloatingLicensePool) -> None:
        self._pools[pool.firm_id] = pool

    def get(self, firm_id: str) -> FloatingLicensePool | None:
        return self._pools.get(firm_id)
