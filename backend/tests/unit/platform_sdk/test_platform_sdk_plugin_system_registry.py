from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus


def _manifest(plugin_id: str = "p1", plugin_type: PluginType = PluginType.AGENT) -> PluginManifest:
    return PluginManifest(
        id=plugin_id,
        name="Plugin 1",
        version="1.0.0",
        plugin_type=plugin_type,
        author="a",
        description="...",
        license="MIT",
    )


def test_manifest_starts_in_development() -> None:
    manifest = _manifest()

    assert manifest.status is PublishingStatus.DEVELOPMENT
    assert manifest.signature is None


def test_registry_register_and_get() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())

    assert registry.get("p1") is not None
    assert registry.get("unknown") is None


def test_registry_list_by_type() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest("agent-1", PluginType.AGENT))
    registry.register(_manifest("connector-1", PluginType.CONNECTOR))

    assert [m.id for m in registry.list_by_type(PluginType.AGENT)] == ["agent-1"]


def test_registry_list_all() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest("p1"))
    registry.register(_manifest("p2"))

    assert {m.id for m in registry.list_all()} == {"p1", "p2"}
