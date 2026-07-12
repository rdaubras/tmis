from typing import Protocol

from tmis.identity_platform.configuration.schemas import IdentityConfiguration


class IdentityConfigurationStorePort(Protocol):
    def save(self, configuration: IdentityConfiguration) -> None: ...

    def get(self, firm_id: str) -> IdentityConfiguration | None: ...
