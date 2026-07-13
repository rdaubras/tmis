from tmis.legal_copilot_framework.registry.schemas import CopilotManifest


class InMemoryCopilotRegistryStore:
    def __init__(self) -> None:
        self._history: dict[str, list[CopilotManifest]] = {}

    def save(self, manifest: CopilotManifest) -> None:
        self._history.setdefault(manifest.copilot_id, []).append(manifest)

    def history(self, copilot_id: str) -> list[CopilotManifest]:
        return list(self._history.get(copilot_id, []))

    def list_copilot_ids(self) -> list[str]:
        return list(self._history.keys())
