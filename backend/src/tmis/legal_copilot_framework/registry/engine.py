from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus
from tmis.legal_copilot_framework.registry.ports import CopilotRegistryStorePort
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest


class CopilotRegistry:
    """The central catalog. Supports several versions of the same
    copilot simultaneously — `history()` never drops an entry,
    `get_latest()` is a read-time choice, not a storage decision."""

    def __init__(self, store: CopilotRegistryStorePort) -> None:
        self._store = store

    def register(self, manifest: CopilotManifest) -> CopilotManifest:
        self._store.save(manifest)
        return manifest

    def get(self, copilot_id: str, version: str | None = None) -> CopilotManifest:
        history = self._store.history(copilot_id)
        if not history:
            raise KeyError(copilot_id)
        if version is None:
            return history[-1]
        for manifest in history:
            if manifest.version == version:
                return manifest
        raise KeyError(f"{copilot_id}@{version}")

    def get_latest(self, copilot_id: str) -> CopilotManifest:
        return self.get(copilot_id)

    def list_versions(self, copilot_id: str) -> list[CopilotManifest]:
        return self._store.history(copilot_id)

    def history(self, copilot_id: str) -> list[CopilotManifest]:
        return self._store.history(copilot_id)

    def list_all(self) -> list[CopilotManifest]:
        return [self.get_latest(cid) for cid in self._store.list_copilot_ids()]

    def set_status(self, copilot_id: str, version: str, status: CopilotStatus) -> CopilotManifest:
        manifest = self.get(copilot_id, version)
        manifest.status = status
        self._store.save(manifest)
        return manifest
