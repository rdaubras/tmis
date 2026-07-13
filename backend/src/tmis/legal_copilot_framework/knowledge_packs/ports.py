from typing import Protocol

from tmis.legal_copilot_framework.knowledge_packs.schemas import KnowledgePack


class KnowledgePackStorePort(Protocol):
    def save(self, pack: KnowledgePack) -> None: ...

    def get(self, pack_id: str, version: int | None = None) -> KnowledgePack | None: ...

    def history(self, pack_id: str) -> list[KnowledgePack]: ...
