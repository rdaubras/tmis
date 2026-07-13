from tmis.legal_copilot_framework.prompt_packs.schemas import PromptPack


class InMemoryPromptPackStore:
    """Keeps every version ever registered, same convention as
    `ai.prompts.PromptRegistry` and `legal_drafting.templates.
    TemplateRegistry`."""

    def __init__(self) -> None:
        self._history: dict[str, list[PromptPack]] = {}

    def save(self, pack: PromptPack) -> None:
        self._history.setdefault(pack.id, []).append(pack)

    def get(self, pack_id: str, version: int | None = None) -> PromptPack | None:
        versions = self._history.get(pack_id)
        if not versions:
            return None
        if version is None:
            return versions[-1]
        for pack in versions:
            if pack.version == version:
                return pack
        return None

    def history(self, pack_id: str) -> list[PromptPack]:
        return list(self._history.get(pack_id, []))
