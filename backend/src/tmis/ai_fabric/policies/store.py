from tmis.ai_fabric.policies.schemas import Policy


class InMemoryPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def add(self, policy: Policy) -> None:
        self._policies[policy.id] = policy

    def list_for_model(self, model_name: str) -> list[Policy]:
        return [
            p
            for p in self._policies.values()
            if p.active and p.model_name in (model_name, "*")
        ]

    def list_all(self) -> list[Policy]:
        return list(self._policies.values())

    def deactivate(self, policy_id: str) -> None:
        policy = self._policies.get(policy_id)
        if policy is not None:
            policy.active = False
