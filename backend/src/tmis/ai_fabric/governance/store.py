from tmis.ai_fabric.governance.schemas import PolicyDecision


class InMemoryGovernanceStore:
    def __init__(self) -> None:
        self._decisions: list[PolicyDecision] = []

    def append(self, decision: PolicyDecision) -> None:
        self._decisions.append(decision)

    def history(self, firm_id: str, model_name: str) -> list[PolicyDecision]:
        return [
            d for d in self._decisions if d.firm_id == firm_id and d.model_name == model_name
        ]
