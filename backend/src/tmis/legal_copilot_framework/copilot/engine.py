from datetime import UTC, datetime

from tmis.legal_copilot_framework.copilot.ports import CopilotActivationStorePort, CopilotStorePort
from tmis.legal_copilot_framework.copilot.schemas import CopilotActivation, LegalCopilot


class CopilotEngine:
    """Owns the assembled `LegalCopilot` catalog and per-firm
    activation state. Definition (`define`) is normally called by
    `sdk.CopilotBuilder`, never directly with hand-built pack ids —
    this engine trusts the ids it is given were already validated."""

    def __init__(self, store: CopilotStorePort, activations: CopilotActivationStorePort) -> None:
        self._store = store
        self._activations = activations

    def define(self, copilot: LegalCopilot) -> LegalCopilot:
        self._store.save(copilot)
        return copilot

    def get(self, copilot_id: str) -> LegalCopilot:
        copilot = self._store.get(copilot_id)
        if copilot is None:
            raise KeyError(copilot_id)
        return copilot

    def list_all(self) -> list[LegalCopilot]:
        return self._store.list_all()

    def activate(self, firm_id: str, copilot_id: str) -> CopilotActivation:
        self.get(copilot_id)  # raises if unknown
        activation = CopilotActivation(firm_id=firm_id, copilot_id=copilot_id, active=True)
        self._activations.save(activation)
        return activation

    def deactivate(self, firm_id: str, copilot_id: str) -> CopilotActivation:
        activation = CopilotActivation(
            firm_id=firm_id,
            copilot_id=copilot_id,
            active=False,
            updated_at=datetime.now(UTC),
        )
        self._activations.save(activation)
        return activation

    def is_active(self, firm_id: str, copilot_id: str) -> bool:
        activation = self._activations.get(firm_id, copilot_id)
        return activation is not None and activation.active

    def active_copilots(self, firm_id: str) -> list[LegalCopilot]:
        return [
            self.get(a.copilot_id)
            for a in self._activations.list_for_firm(firm_id)
            if a.active
        ]
