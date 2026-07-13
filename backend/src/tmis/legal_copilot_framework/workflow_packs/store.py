from tmis.legal_copilot_framework.workflow_packs.schemas import WorkflowPack


class InMemoryWorkflowPackStore:
    def __init__(self) -> None:
        self._history: dict[str, list[WorkflowPack]] = {}

    def save(self, pack: WorkflowPack) -> None:
        self._history.setdefault(pack.id, []).append(pack)

    def get(self, pack_id: str, version: int | None = None) -> WorkflowPack | None:
        versions = self._history.get(pack_id)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for pack in versions:
            if pack.version == version:
                return pack
        return None

    def history(self, pack_id: str) -> list[WorkflowPack]:
        return list(self._history.get(pack_id, []))
