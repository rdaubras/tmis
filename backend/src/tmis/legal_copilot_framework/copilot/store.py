from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot


class InMemoryCopilotStore:
    def __init__(self) -> None:
        self._copilots: dict[str, LegalCopilot] = {}

    def save(self, copilot: LegalCopilot) -> None:
        self._copilots[copilot.id] = copilot

    def get(self, copilot_id: str) -> LegalCopilot | None:
        return self._copilots.get(copilot_id)

    def list_all(self) -> list[LegalCopilot]:
        return list(self._copilots.values())
