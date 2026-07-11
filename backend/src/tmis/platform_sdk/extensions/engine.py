from datetime import UTC, datetime

import structlog

from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform_sdk.extensions.ports import ExtensionStorePort
from tmis.platform_sdk.extensions.schemas import (
    ExtensionInstance,
    ExtensionStatus,
    new_extension_id,
)
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PublishingStatus

_logger = structlog.get_logger(__name__)


class PluginNotAvailableError(ValueError):
    pass


class UngrantablePermissionError(ValueError):
    pass


class ExtensionEngine:
    """Per-cabinet installation lifecycle — the sprint's "Marketplace"
    spec items téléchargement/installation/mise à jour/désinstallation,
    scoped by `firm_id` (multi-tenant, see `tmis.platform.security.
    tenant_isolation` conventions established since Sprint 10)."""

    def __init__(
        self,
        store: ExtensionStorePort,
        registry: PluginRegistryPort,
        permissions: PermissionEngine,
    ) -> None:
        self._store = store
        self._registry = registry
        self._permissions = permissions

    def install(
        self,
        firm_id: str,
        plugin_id: str,
        requested_permissions: frozenset[ExtensionPermission],
    ) -> ExtensionInstance:
        manifest = self._registry.get(plugin_id)
        if manifest is None or manifest.status is not PublishingStatus.PUBLISHED:
            raise PluginNotAvailableError(f"{plugin_id} is not published")
        declared = frozenset(ExtensionPermission(p) for p in manifest.permissions)
        if not requested_permissions <= declared:
            raise UngrantablePermissionError(
                f"{plugin_id} only declares {sorted(p.value for p in declared)}"
            )
        instance = ExtensionInstance(
            id=new_extension_id(),
            firm_id=firm_id,
            plugin_id=plugin_id,
            version=manifest.version,
            granted_permissions=requested_permissions,
        )
        self._store.save(instance)
        self._permissions.grant(firm_id, plugin_id, requested_permissions)
        _logger.info(
            "platform_sdk.extension_installed",
            firm_id=firm_id,
            plugin_id=plugin_id,
            version=manifest.version,
        )
        get_metrics_registry().counter(
            "platform_sdk_installs_total", "Total plugin installations"
        ).inc(plugin_id=plugin_id)
        return instance

    def uninstall(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        instance = self._get(firm_id, plugin_id)
        instance.status = ExtensionStatus.UNINSTALLED
        instance.updated_at = datetime.now(UTC)
        self._store.save(instance)
        self._permissions.revoke(firm_id, plugin_id)
        _logger.info("platform_sdk.extension_uninstalled", firm_id=firm_id, plugin_id=plugin_id)
        get_metrics_registry().counter(
            "platform_sdk_uninstalls_total", "Total plugin uninstallations"
        ).inc(plugin_id=plugin_id)
        return instance

    def enable(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        return self._set_status(firm_id, plugin_id, ExtensionStatus.ACTIVE)

    def disable(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        return self._set_status(firm_id, plugin_id, ExtensionStatus.DISABLED)

    def update(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        """Re-syncs the installed instance to the manifest's current
        published version — this sprint keeps a single manifest per
        plugin id (version bumped in place, mirroring
        `tmis.cabinet_knowledge.knowledge.KnowledgeObject.version`),
        so "updating" an installation means picking up that new
        version string rather than switching between stored release
        artifacts; see docs/65-architecture-platform-sdk.md."""
        manifest = self._registry.get(plugin_id)
        if manifest is None:
            raise KeyError(plugin_id)
        instance = self._get(firm_id, plugin_id)
        instance.version = manifest.version
        instance.updated_at = datetime.now(UTC)
        self._store.save(instance)
        return instance

    def list_for_firm(self, firm_id: str) -> list[ExtensionInstance]:
        return self._store.list_for_firm(firm_id)

    def list_all(self) -> list[ExtensionInstance]:
        return self._store.list_all()

    def _get(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        instance = self._store.get(firm_id, plugin_id)
        if instance is None:
            raise KeyError((firm_id, plugin_id))
        return instance

    def _set_status(
        self, firm_id: str, plugin_id: str, status: ExtensionStatus
    ) -> ExtensionInstance:
        instance = self._get(firm_id, plugin_id)
        instance.status = status
        instance.updated_at = datetime.now(UTC)
        self._store.save(instance)
        return instance
