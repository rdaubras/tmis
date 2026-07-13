from tmis.legal_copilot_framework.reasoning_packs.schemas import ReasoningPack


class InMemoryReasoningPackStore:
    def __init__(self) -> None:
        self._history: dict[str, list[ReasoningPack]] = {}

    def save(self, pack: ReasoningPack) -> None:
        self._history.setdefault(pack.id, []).append(pack)

    def get(self, pack_id: str, version: int | None = None) -> ReasoningPack | None:
        versions = self._history.get(pack_id)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for pack in versions:
            if pack.version == version:
                return pack
        return None

    def history(self, pack_id: str) -> list[ReasoningPack]:
        return list(self._history.get(pack_id, []))
