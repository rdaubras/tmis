from typing import Protocol

from tmis.business_platform.tenant_settings.schemas import TenantSettings


class TenantSettingsStorePort(Protocol):
    def save(self, settings: TenantSettings) -> None: ...

    def get(self, firm_id: str) -> TenantSettings | None: ...
