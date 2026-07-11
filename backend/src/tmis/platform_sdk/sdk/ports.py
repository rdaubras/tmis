from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from tmis.platform_sdk.plugin_system.schemas import PluginType

if TYPE_CHECKING:
    from tmis.platform_sdk.sdk.schemas import PluginContext


class EventPublisherPort(Protocol):
    """The only way a plugin can publish a platform event — narrow on
    purpose, satisfied in production by
    `tmis.platform_sdk.events_sdk.PlatformEventBus`."""

    async def publish(self, event_name: str, payload: dict[str, Any]) -> None: ...


class PermissionCheckerPort(Protocol):
    """The only way a plugin can check whether it may act — satisfied
    in production by `tmis.platform_sdk.permissions.PermissionEngine`,
    always scoped to the plugin/firm pair of the current
    `PluginContext`."""

    def has_permission(self, permission: str) -> bool: ...


class PluginPort(Protocol):
    """The single uniform contract `tmis.platform_sdk.sandbox` and
    `tmis.platform_sdk.plugin_loader` invoke, regardless of plugin
    type — every `*_sdk` base class (agent, connector, workflow,
    document template) implements `invoke()` as a thin adapter to a
    more ergonomic, type-specific method plugin authors actually
    override (see `tmis.platform_sdk.agent_sdk.BaseAgentPlugin.run`
    for an example). Keeping one narrow entry point here means the
    sandbox never needs to know the specifics of any plugin type."""

    id: str
    plugin_type: PluginType

    async def invoke(self, context: PluginContext, payload: dict[str, Any]) -> dict[str, Any]: ...
