from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.schemas import Policy


class InMemoryPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def save(self, policy: Policy) -> None:
        self._policies[policy.id] = policy

    def list_for_permission(self, firm_id: str, permission: Permission) -> list[Policy]:
        return [
            p
            for p in self._policies.values()
            if p.firm_id == firm_id and p.permission == permission and p.active
        ]

    def list_for_firm(self, firm_id: str) -> list[Policy]:
        return [p for p in self._policies.values() if p.firm_id == firm_id]
