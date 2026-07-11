from tmis.platform_sdk.permissions.schemas import ExtensionPermission


class InMemoryPermissionStore:
    def __init__(self) -> None:
        self._grants: dict[tuple[str, str], frozenset[ExtensionPermission]] = {}

    def grant(
        self, firm_id: str, plugin_id: str, permissions: frozenset[ExtensionPermission]
    ) -> None:
        self._grants[(firm_id, plugin_id)] = permissions

    def revoke(self, firm_id: str, plugin_id: str) -> None:
        self._grants.pop((firm_id, plugin_id), None)

    def granted(self, firm_id: str, plugin_id: str) -> frozenset[ExtensionPermission]:
        return self._grants.get((firm_id, plugin_id), frozenset())
