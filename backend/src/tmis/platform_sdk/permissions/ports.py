from typing import Protocol

from tmis.platform_sdk.permissions.schemas import ExtensionPermission


class PermissionStorePort(Protocol):
    def grant(
        self, firm_id: str, plugin_id: str, permissions: frozenset[ExtensionPermission]
    ) -> None: ...

    def revoke(self, firm_id: str, plugin_id: str) -> None: ...

    def granted(self, firm_id: str, plugin_id: str) -> frozenset[ExtensionPermission]: ...
