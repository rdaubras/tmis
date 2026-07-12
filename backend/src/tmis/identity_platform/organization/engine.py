from tmis.identity_platform.organization.ports import OrganizationStorePort
from tmis.identity_platform.organization.schemas import Organization, OrganizationStatus


class OrganizationEngine:
    def __init__(self, store: OrganizationStorePort) -> None:
        self._store = store

    def create(self, firm_id: str, legal_name: str) -> Organization:
        organization = Organization(firm_id=firm_id, legal_name=legal_name)
        self._store.save(organization)
        return organization

    def get(self, firm_id: str) -> Organization:
        organization = self._store.get(firm_id)
        if organization is None:
            raise KeyError(firm_id)
        return organization

    def set_status(self, firm_id: str, status: OrganizationStatus) -> Organization:
        organization = self.get(firm_id)
        organization.status = status
        self._store.save(organization)
        return organization

    def list_all(self) -> list[Organization]:
        return self._store.list_all()
