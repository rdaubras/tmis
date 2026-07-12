from typing import Protocol

from tmis.identity_platform.secret_manager.schemas import ManagedSecret


class ManagedSecretStorePort(Protocol):
    def save(self, secret: ManagedSecret) -> None: ...

    def get(self, firm_id: str, key: str) -> ManagedSecret | None: ...

    def list_for_firm(self, firm_id: str) -> list[ManagedSecret]: ...
