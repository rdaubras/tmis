from tmis.platform_sdk.extensions.schemas import ExtensionInstance


class InMemoryExtensionStore:
    def __init__(self) -> None:
        self._instances: dict[tuple[str, str], ExtensionInstance] = {}

    def save(self, instance: ExtensionInstance) -> None:
        self._instances[(instance.firm_id, instance.plugin_id)] = instance

    def get(self, firm_id: str, plugin_id: str) -> ExtensionInstance | None:
        return self._instances.get((firm_id, plugin_id))

    def list_for_firm(self, firm_id: str) -> list[ExtensionInstance]:
        return [i for i in self._instances.values() if i.firm_id == firm_id]

    def list_all(self) -> list[ExtensionInstance]:
        return list(self._instances.values())
