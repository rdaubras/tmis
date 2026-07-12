from tmis.identity_platform.tenant_context.ports import TenantProfileStorePort
from tmis.identity_platform.tenant_context.schemas import TenantBranding, TenantProfile, TenantQuota
from tmis.platform.security.tenant_isolation import (
    TenantAccessError,
    TenantContext,
    require_same_firm,
)

__all__ = [
    "TenantAccessError",
    "TenantContext",
    "TenantContextEngine",
    "require_same_firm",
]


class TenantContextEngine:
    """Owns `TenantProfile` (quota, branding, activation) for every
    firm. Zero Trust boundary checks (`require_same_firm`) are never
    reimplemented here — `TenantContext`/`TenantAccessError`/
    `require_same_firm` are re-exported directly from
    `platform.security.tenant_isolation` (Sprint 10), the canonical
    tenant-isolation primitive every bounded context in TMIS already
    depends on."""

    def __init__(self, store: TenantProfileStorePort) -> None:
        self._store = store

    def provision(
        self,
        firm_id: str,
        quota: TenantQuota | None = None,
        branding: TenantBranding | None = None,
    ) -> TenantProfile:
        profile = TenantProfile(firm_id=firm_id, quota=quota or TenantQuota(), branding=branding)
        self._store.save(profile)
        return profile

    def get(self, firm_id: str) -> TenantProfile | None:
        return self._store.get(firm_id)

    def deactivate(self, firm_id: str) -> TenantProfile:
        profile = self._store.get(firm_id)
        if profile is None:
            raise KeyError(firm_id)
        profile.active = False
        self._store.save(profile)
        return profile

    def activate(self, firm_id: str) -> TenantProfile:
        profile = self._store.get(firm_id)
        if profile is None:
            raise KeyError(firm_id)
        profile.active = True
        self._store.save(profile)
        return profile
