from tmis.platform_sdk.plugin_loader.schemas import PluginFactory


class InMemoryPluginImplementationRegistry:
    """The safe, closed set of plugin implementations known to this
    process — populated exclusively by first-party imports (the
    example plugins, or a real plugin's package registering itself on
    import), never by dynamic code loading."""

    def __init__(self) -> None:
        self._factories: dict[str, PluginFactory] = {}

    def register(self, plugin_id: str, factory: PluginFactory) -> None:
        self._factories[plugin_id] = factory

    def get(self, plugin_id: str) -> PluginFactory | None:
        return self._factories.get(plugin_id)
