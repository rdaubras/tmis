from typing import Protocol

from tmis.legal_copilot_framework.document_packs.schemas import DocumentPack


class DocumentPackStorePort(Protocol):
    def save(self, pack: DocumentPack) -> None: ...

    def get(self, pack_id: str, version: int | None = None) -> DocumentPack | None: ...

    def history(self, pack_id: str) -> list[DocumentPack]: ...
