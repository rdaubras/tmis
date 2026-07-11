from dataclasses import dataclass

from tmis.platform_sdk.permissions.ports import PermissionStorePort
from tmis.platform_sdk.permissions.schemas import ExtensionPermission


@dataclass(frozen=True, slots=True)
class _ScopedPermissionChecker:
    """Satisfies `tmis.platform_sdk.sdk.ports.PermissionCheckerPort` —
    pre-scoped to one firm/plugin pair so a `PluginContext` can expose
    `has_permission(permission)` without leaking `firm_id`/`plugin_id`
    into every call site."""

    engine: "PermissionEngine"
    firm_id: str
    plugin_id: str

    def has_permission(self, permission: str) -> bool:
        return self.engine.check(self.firm_id, self.plugin_id, ExtensionPermission(permission))


class PermissionEngine:
    """The sprint's "PERMISSION ENGINE" — every permission an
    extension holds must have been explicitly granted at install time
    (see `tmis.platform_sdk.extensions.ExtensionEngine.install`),
    never inferred or defaulted to "all"."""

    def __init__(self, store: PermissionStorePort) -> None:
        self._store = store

    def grant(
        self, firm_id: str, plugin_id: str, permissions: frozenset[ExtensionPermission]
    ) -> None:
        self._store.grant(firm_id, plugin_id, permissions)

    def revoke(self, firm_id: str, plugin_id: str) -> None:
        self._store.revoke(firm_id, plugin_id)

    def check(self, firm_id: str, plugin_id: str, permission: ExtensionPermission) -> bool:
        return permission in self._store.granted(firm_id, plugin_id)

    def granted(self, firm_id: str, plugin_id: str) -> frozenset[ExtensionPermission]:
        return self._store.granted(firm_id, plugin_id)

    def checker_for(self, firm_id: str, plugin_id: str) -> _ScopedPermissionChecker:
        return _ScopedPermissionChecker(self, firm_id, plugin_id)
