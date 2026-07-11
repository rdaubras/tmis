from tmis.ai_governance.policy_engine.schemas import GovernancePolicy


class InMemoryGovernancePolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, GovernancePolicy] = {}

    def add(self, policy: GovernancePolicy) -> None:
        self._policies[policy.id] = policy

    def list_for_firm(self, firm_id: str) -> list[GovernancePolicy]:
        return [p for p in self._policies.values() if p.active and p.firm_id == firm_id]

    def deactivate(self, policy_id: str) -> None:
        policy = self._policies.get(policy_id)
        if policy is not None:
            policy.active = False
