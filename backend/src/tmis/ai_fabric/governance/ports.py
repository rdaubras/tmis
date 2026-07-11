from typing import Protocol

from tmis.ai_fabric.governance.schemas import PolicyDecision


class GovernanceStorePort(Protocol):
    def append(self, decision: PolicyDecision) -> None: ...

    def history(self, firm_id: str, model_name: str) -> list[PolicyDecision]: ...
