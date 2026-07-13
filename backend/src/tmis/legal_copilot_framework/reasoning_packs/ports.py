from typing import Protocol

from tmis.legal_copilot_framework.reasoning_packs.schemas import ReasoningPack


class ReasoningPackStorePort(Protocol):
    def save(self, pack: ReasoningPack) -> None: ...

    def get(self, pack_id: str, version: int | None = None) -> ReasoningPack | None: ...

    def history(self, pack_id: str) -> list[ReasoningPack]: ...
