from typing import Protocol

from tmis.ai_governance.policy_engine.schemas import GovernancePolicy


class GovernancePolicyStorePort(Protocol):
    def add(self, policy: GovernancePolicy) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[GovernancePolicy]: ...

    def deactivate(self, policy_id: str) -> None: ...
