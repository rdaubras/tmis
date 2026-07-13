from typing import Protocol

from tmis.legal_copilot_framework.workflow_packs.schemas import WorkflowPack


class WorkflowPackStorePort(Protocol):
    def save(self, pack: WorkflowPack) -> None: ...

    def get(self, pack_id: str, version: int | None = None) -> WorkflowPack | None: ...

    def history(self, pack_id: str) -> list[WorkflowPack]: ...
