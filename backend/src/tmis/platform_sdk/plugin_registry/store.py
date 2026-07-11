from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType


class InMemoryPluginRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, PluginManifest] = {}

    def register(self, manifest: PluginManifest) -> None:
        self._manifests[manifest.id] = manifest

    def get(self, plugin_id: str) -> PluginManifest | None:
        return self._manifests.get(plugin_id)

    def list_all(self) -> list[PluginManifest]:
        return list(self._manifests.values())

    def list_by_type(self, plugin_type: PluginType) -> list[PluginManifest]:
        return [m for m in self._manifests.values() if m.plugin_type is plugin_type]
