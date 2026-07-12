from typing import Protocol

from tmis.identity_platform.tenant_context.schemas import TenantProfile


class TenantProfileStorePort(Protocol):
    def save(self, profile: TenantProfile) -> None: ...

    def get(self, firm_id: str) -> TenantProfile | None: ...

    def list_all(self) -> list[TenantProfile]: ...
