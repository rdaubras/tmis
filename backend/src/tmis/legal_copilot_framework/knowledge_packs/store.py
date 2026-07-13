from tmis.legal_copilot_framework.knowledge_packs.schemas import KnowledgePack


class InMemoryKnowledgePackStore:
    def __init__(self) -> None:
        self._history: dict[str, list[KnowledgePack]] = {}

    def save(self, pack: KnowledgePack) -> None:
        self._history.setdefault(pack.id, []).append(pack)

    def get(self, pack_id: str, version: int | None = None) -> KnowledgePack | None:
        versions = self._history.get(pack_id)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for pack in versions:
            if pack.version == version:
                return pack
        return None

    def history(self, pack_id: str) -> list[KnowledgePack]:
        return list(self._history.get(pack_id, []))
