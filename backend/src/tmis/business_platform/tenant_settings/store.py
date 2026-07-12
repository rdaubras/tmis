from tmis.business_platform.tenant_settings.schemas import TenantSettings


class InMemoryTenantSettingsStore:
    def __init__(self) -> None:
        self._settings: dict[str, TenantSettings] = {}

    def save(self, settings: TenantSettings) -> None:
        self._settings[settings.firm_id] = settings

    def get(self, firm_id: str) -> TenantSettings | None:
        return self._settings.get(firm_id)
