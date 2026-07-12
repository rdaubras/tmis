from tmis.identity_platform.organization.schemas import Organization


class InMemoryOrganizationStore:
    def __init__(self) -> None:
        self._organizations: dict[str, Organization] = {}

    def save(self, organization: Organization) -> None:
        self._organizations[organization.firm_id] = organization

    def get(self, firm_id: str) -> Organization | None:
        return self._organizations.get(firm_id)

    def list_all(self) -> list[Organization]:
        return list(self._organizations.values())
