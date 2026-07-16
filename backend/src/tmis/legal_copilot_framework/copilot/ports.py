from typing import Protocol

from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot


class CopilotStorePort(Protocol):
    def save(self, copilot: LegalCopilot) -> None: ...

    def get(self, copilot_id: str) -> LegalCopilot | None: ...

    def list_all(self) -> list[LegalCopilot]: ...
