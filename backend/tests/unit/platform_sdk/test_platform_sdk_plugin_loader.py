import pytest

from tmis.platform_sdk.plugin_loader.engine import (
    PluginImplementationMissingError,
    PluginLoader,
    PluginNotPublishedError,
)
from tmis.platform_sdk.plugin_loader.store import InMemoryPluginImplementationRegistry
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus


def _manifest(status: PublishingStatus = PublishingStatus.PUBLISHED) -> PluginManifest:
    manifest = PluginManifest(
        id="p1",
        name="Plugin 1",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        author="a",
        description="...",
        license="MIT",
    )
    manifest.status = status
    return manifest


class _FakePlugin:
    id = "p1"
    plugin_type = PluginType.AGENT

    async def invoke(self, context: object, payload: dict) -> dict:  # type: ignore[type-arg]
        return {}


def test_load_raises_for_unknown_plugin() -> None:
    loader = PluginLoader(InMemoryPluginRegistry(), InMemoryPluginImplementationRegistry())

    with pytest.raises(KeyError):
        loader.load("unknown")


def test_load_raises_when_not_published() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest(status=PublishingStatus.DEVELOPMENT))
    loader = PluginLoader(registry, InMemoryPluginImplementationRegistry())

    with pytest.raises(PluginNotPublishedError):
        loader.load("p1")


def test_load_raises_when_implementation_missing() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    loader = PluginLoader(registry, InMemoryPluginImplementationRegistry())

    with pytest.raises(PluginImplementationMissingError):
        loader.load("p1")


def test_load_returns_instance_when_available() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    implementations = InMemoryPluginImplementationRegistry()
    implementations.register("p1", _FakePlugin)
    loader = PluginLoader(registry, implementations)

    plugin = loader.load("p1")

    assert isinstance(plugin, _FakePlugin)
