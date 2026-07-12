from tmis.identity_platform.tenant_context.schemas import TenantProfile


class InMemoryTenantProfileStore:
    def __init__(self) -> None:
        self._profiles: dict[str, TenantProfile] = {}

    def save(self, profile: TenantProfile) -> None:
        self._profiles[profile.firm_id] = profile

    def get(self, firm_id: str) -> TenantProfile | None:
        return self._profiles.get(firm_id)

    def list_all(self) -> list[TenantProfile]:
        return list(self._profiles.values())
