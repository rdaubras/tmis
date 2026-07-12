from tmis.business_platform.modules.schemas import ModuleActivation, TmisModule


class InMemoryModuleActivationStore:
    def __init__(self) -> None:
        self._activations: dict[tuple[str, TmisModule], ModuleActivation] = {}

    def save(self, activation: ModuleActivation) -> None:
        self._activations[(activation.firm_id, activation.module)] = activation

    def get(self, firm_id: str, module: TmisModule) -> ModuleActivation | None:
        return self._activations.get((firm_id, module))

    def list_for_firm(self, firm_id: str) -> list[ModuleActivation]:
        return [a for (fid, _), a in self._activations.items() if fid == firm_id]
