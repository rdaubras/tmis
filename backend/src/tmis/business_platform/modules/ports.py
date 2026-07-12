from typing import Protocol

from tmis.business_platform.modules.schemas import ModuleActivation, TmisModule


class ModuleActivationStorePort(Protocol):
    def save(self, activation: ModuleActivation) -> None: ...

    def get(self, firm_id: str, module: TmisModule) -> ModuleActivation | None: ...

    def list_for_firm(self, firm_id: str) -> list[ModuleActivation]: ...
