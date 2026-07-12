from typing import Protocol

from tmis.identity_platform.organization.schemas import Organization


class OrganizationStorePort(Protocol):
    def save(self, organization: Organization) -> None: ...

    def get(self, firm_id: str) -> Organization | None: ...

    def list_all(self) -> list[Organization]: ...
