from typing import Protocol

from tmis.legal_copilot_framework.registry.schemas import CopilotManifest


class CopilotRegistryStorePort(Protocol):
    def save(self, manifest: CopilotManifest) -> None: ...

    def history(self, copilot_id: str) -> list[CopilotManifest]: ...

    def list_copilot_ids(self) -> list[str]: ...
