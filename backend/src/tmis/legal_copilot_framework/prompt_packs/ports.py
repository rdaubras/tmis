from typing import Protocol

from tmis.legal_copilot_framework.prompt_packs.schemas import PromptPack


class PromptPackStorePort(Protocol):
    def save(self, pack: PromptPack) -> None: ...

    def get(self, pack_id: str, version: int | None = None) -> PromptPack | None: ...

    def history(self, pack_id: str) -> list[PromptPack]: ...
