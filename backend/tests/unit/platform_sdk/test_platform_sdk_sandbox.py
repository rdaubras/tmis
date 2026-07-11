import asyncio

from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_loader.engine import PluginLoader
from tmis.platform_sdk.plugin_loader.store import InMemoryPluginImplementationRegistry
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus
from tmis.platform_sdk.sandbox.engine import SandboxExecutor
from tmis.platform_sdk.sandbox.schemas import ResourceQuota

FIRM = "firm-a"
PLUGIN = "p1"


class _EchoPlugin:
    id = PLUGIN
    plugin_type = PluginType.AGENT

    async def invoke(self, context: object, payload: dict) -> dict:  # type: ignore[type-arg]
        return {"echo": payload}


class _SlowPlugin:
    id = PLUGIN
    plugin_type = PluginType.AGENT

    async def invoke(self, context: object, payload: dict) -> dict:  # type: ignore[type-arg]
        await asyncio.sleep(10)
        return {}


class _FailingPlugin:
    id = PLUGIN
    plugin_type = PluginType.AGENT

    async def invoke(self, context: object, payload: dict) -> dict:  # type: ignore[type-arg]
        raise RuntimeError("boom")


class _NullEvents:
    async def publish(self, event_name: str, payload: dict) -> None:  # type: ignore[type-arg]
        pass


def _published_manifest() -> PluginManifest:
    manifest = PluginManifest(
        id=PLUGIN,
        name="Plugin 1",
        version="1.0.0",
        plugin_type=PluginType.AGENT,
        author="a",
        description="...",
        license="MIT",
    )
    manifest.status = PublishingStatus.PUBLISHED
    return manifest


def _build_executor(
    plugin_class: type, quota: ResourceQuota = ResourceQuota()
) -> SandboxExecutor:
    registry = InMemoryPluginRegistry()
    registry.register(_published_manifest())
    implementations = InMemoryPluginImplementationRegistry()
    implementations.register(PLUGIN, plugin_class)
    loader = PluginLoader(registry, implementations)
    permissions = PermissionEngine(InMemoryPermissionStore())
    permissions.grant(FIRM, PLUGIN, frozenset({ExtensionPermission.READ_CASES}))
    return SandboxExecutor(loader, permissions, _NullEvents(), quota=quota)


async def test_execute_denies_without_granted_permission() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published_manifest())
    implementations = InMemoryPluginImplementationRegistry()
    implementations.register(PLUGIN, _EchoPlugin)
    loader = PluginLoader(registry, implementations)
    permissions = PermissionEngine(InMemoryPermissionStore())
    executor = SandboxExecutor(loader, permissions, _NullEvents())

    result = await executor.execute(
        FIRM, "avocat1", PLUGIN, {}, ExtensionPermission.MANAGE_USERS
    )

    assert result.success is False
    assert result.error == "permission refusée"


async def test_execute_succeeds_and_returns_result() -> None:
    executor = _build_executor(_EchoPlugin)

    result = await executor.execute(
        FIRM, "avocat1", PLUGIN, {"x": 1}, ExtensionPermission.READ_CASES
    )

    assert result.success is True
    assert result.result == {"echo": {"x": 1}}


async def test_execute_times_out() -> None:
    executor = _build_executor(_SlowPlugin, quota=ResourceQuota(max_execution_seconds=0.05))

    result = await executor.execute(FIRM, "avocat1", PLUGIN, {}, ExtensionPermission.READ_CASES)

    assert result.success is False
    assert result.error == "délai dépassé"


async def test_execute_catches_plugin_exceptions() -> None:
    executor = _build_executor(_FailingPlugin)

    result = await executor.execute(FIRM, "avocat1", PLUGIN, {}, ExtensionPermission.READ_CASES)

    assert result.success is False
    assert result.error == "boom"


async def test_execute_enforces_call_quota() -> None:
    executor = _build_executor(_EchoPlugin, quota=ResourceQuota(max_calls_per_minute=2))

    for _ in range(2):
        result = await executor.execute(
            FIRM, "avocat1", PLUGIN, {}, ExtensionPermission.READ_CASES
        )
        assert result.success is True

    third = await executor.execute(FIRM, "avocat1", PLUGIN, {}, ExtensionPermission.READ_CASES)

    assert third.success is False
    assert third.error == "quota d'appels dépassé"
