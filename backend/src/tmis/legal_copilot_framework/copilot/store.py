from tmis.legal_copilot_framework.copilot.schemas import CopilotActivation, LegalCopilot


class InMemoryCopilotStore:
    def __init__(self) -> None:
        self._copilots: dict[str, LegalCopilot] = {}

    def save(self, copilot: LegalCopilot) -> None:
        self._copilots[copilot.id] = copilot

    def get(self, copilot_id: str) -> LegalCopilot | None:
        return self._copilots.get(copilot_id)

    def list_all(self) -> list[LegalCopilot]:
        return list(self._copilots.values())


class InMemoryCopilotActivationStore:
    def __init__(self) -> None:
        self._activations: dict[tuple[str, str], CopilotActivation] = {}

    def save(self, activation: CopilotActivation) -> None:
        self._activations[(activation.firm_id, activation.copilot_id)] = activation

    def get(self, firm_id: str, copilot_id: str) -> CopilotActivation | None:
        return self._activations.get((firm_id, copilot_id))

    def list_for_firm(self, firm_id: str) -> list[CopilotActivation]:
        return [a for (fid, _), a in self._activations.items() if fid == firm_id]
