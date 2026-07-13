from tmis.legal_copilot_framework.document_packs.schemas import DocumentPack


class InMemoryDocumentPackStore:
    def __init__(self) -> None:
        self._history: dict[str, list[DocumentPack]] = {}

    def save(self, pack: DocumentPack) -> None:
        self._history.setdefault(pack.id, []).append(pack)

    def get(self, pack_id: str, version: int | None = None) -> DocumentPack | None:
        versions = self._history.get(pack_id)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for pack in versions:
            if pack.version == version:
                return pack
        return None

    def history(self, pack_id: str) -> list[DocumentPack]:
        return list(self._history.get(pack_id, []))
