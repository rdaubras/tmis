from tmis.platform.licensing.schemas import License


class InMemoryLicenseStore:
    def __init__(self) -> None:
        self._licenses: dict[str, License] = {}

    def save(self, license_: License) -> None:
        self._licenses[license_.id] = license_

    def get(self, license_id: str) -> License | None:
        return self._licenses.get(license_id)

    def get_for_firm(self, firm_id: str) -> License | None:
        for license_ in self._licenses.values():
            if license_.firm_id == firm_id:
                return license_
        return None
