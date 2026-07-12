from tmis.identity_platform.delegation.schemas import Delegation


class InMemoryDelegationStore:
    def __init__(self) -> None:
        self._delegations: dict[tuple[str, str], Delegation] = {}

    def save(self, delegation: Delegation) -> None:
        self._delegations[(delegation.firm_id, delegation.id)] = delegation

    def get(self, firm_id: str, delegation_id: str) -> Delegation | None:
        return self._delegations.get((firm_id, delegation_id))

    def list_for_delegate(self, firm_id: str, delegate_id: str) -> list[Delegation]:
        return [
            d
            for d in self._delegations.values()
            if d.firm_id == firm_id and d.delegate_id == delegate_id
        ]

    def list_for_firm(self, firm_id: str) -> list[Delegation]:
        return [d for d in self._delegations.values() if d.firm_id == firm_id]
