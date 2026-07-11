import pytest

from tmis.platform_sdk.extensions.engine import (
    ExtensionEngine,
    PluginNotAvailableError,
    UngrantablePermissionError,
)
from tmis.platform_sdk.extensions.schemas import ExtensionStatus
from tmis.platform_sdk.extensions.store import InMemoryExtensionStore
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus

FIRM = "firm-a"
PLUGIN = "p1"


def _published_manifest(
    permissions: frozenset[str] = frozenset({"read_cases", "read_documents"}),
) -> PluginManifest:
    manifest = PluginManifest(
        id=PLUGIN,
        name="Plugin 1",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        author="a",
        description="...",
        license="MIT",
        permissions=permissions,
    )
    manifest.status = PublishingStatus.PUBLISHED
    return manifest


def _engine(manifest: PluginManifest | None = None) -> ExtensionEngine:
    registry = InMemoryPluginRegistry()
    registry.register(manifest or _published_manifest())
    permissions = PermissionEngine(InMemoryPermissionStore())
    return ExtensionEngine(InMemoryExtensionStore(), registry, permissions)


def test_install_requires_published_plugin() -> None:
    manifest = _published_manifest()
    manifest.status = PublishingStatus.DEVELOPMENT
    engine = _engine(manifest)

    with pytest.raises(PluginNotAvailableError):
        engine.install(FIRM, PLUGIN, frozenset())


def test_install_rejects_undeclared_permissions() -> None:
    engine = _engine(_published_manifest(permissions=frozenset({"read_cases"})))

    with pytest.raises(UngrantablePermissionError):
        engine.install(FIRM, PLUGIN, frozenset({ExtensionPermission.MANAGE_USERS}))


def test_install_grants_only_requested_permissions() -> None:
    engine = _engine()

    instance = engine.install(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))

    assert instance.granted_permissions == frozenset({ExtensionPermission.READ_CASES})
    assert instance.status is ExtensionStatus.ACTIVE


def test_uninstall_revokes_permissions() -> None:
    engine = _engine()
    engine.install(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))

    engine.uninstall(FIRM, PLUGIN)

    instances = engine.list_for_firm(FIRM)
    assert instances[0].status is ExtensionStatus.UNINSTALLED


def test_disable_then_enable() -> None:
    engine = _engine()
    engine.install(FIRM, PLUGIN, frozenset())

    disabled = engine.disable(FIRM, PLUGIN)
    assert disabled.status is ExtensionStatus.DISABLED

    enabled = engine.enable(FIRM, PLUGIN)
    assert enabled.status is ExtensionStatus.ACTIVE


def test_list_for_firm_is_scoped() -> None:
    engine = _engine()
    engine.install(FIRM, PLUGIN, frozenset())

    assert engine.list_for_firm("other-firm") == []
    assert len(engine.list_for_firm(FIRM)) == 1


def test_list_all_spans_every_firm() -> None:
    engine = _engine()
    engine.install(FIRM, PLUGIN, frozenset())
    engine.install("firm-b", PLUGIN, frozenset())

    assert len(engine.list_all()) == 2
