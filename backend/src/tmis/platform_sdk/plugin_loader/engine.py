from tmis.platform_sdk.plugin_loader.store import InMemoryPluginImplementationRegistry
from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PublishingStatus
from tmis.platform_sdk.sdk.ports import PluginPort


class PluginNotPublishedError(ValueError):
    pass


class PluginImplementationMissingError(KeyError):
    pass


class PluginLoader:
    """Resolves a `PluginPort` instance for a manifest — the sprint's
    "PLUGIN LOADER" spec. Refuses to load anything whose manifest
    isn't at least `PUBLISHED` (see `tmis.platform_sdk.publishing`),
    so a plugin still in `DEVELOPMENT`/`VALIDATED`/`SIGNED` can never
    be invoked against a real cabinet's data."""

    def __init__(
        self,
        registry: PluginRegistryPort,
        implementations: InMemoryPluginImplementationRegistry,
    ) -> None:
        self._registry = registry
        self._implementations = implementations

    def load(self, plugin_id: str) -> PluginPort:
        manifest = self._registry.get(plugin_id)
        if manifest is None:
            raise KeyError(plugin_id)
        if manifest.status is not PublishingStatus.PUBLISHED:
            raise PluginNotPublishedError(
                f"{plugin_id} is {manifest.status.value}, expected published"
            )
        factory = self._implementations.get(plugin_id)
        if factory is None:
            raise PluginImplementationMissingError(plugin_id)
        return factory()
