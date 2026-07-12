from datetime import UTC, datetime

from tmis.identity_platform.delegation.ports import DelegationStorePort
from tmis.identity_platform.delegation.schemas import Delegation, new_delegation_id
from tmis.identity_platform.permissions.schemas import Permission


class DelegationEngine:
    def __init__(self, store: DelegationStorePort) -> None:
        self._store = store

    def grant(
        self,
        firm_id: str,
        delegator_id: str,
        delegate_id: str,
        permissions: frozenset[Permission],
        ends_at: datetime,
    ) -> Delegation:
        delegation = Delegation(
            id=new_delegation_id(),
            firm_id=firm_id,
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            permissions=permissions,
            ends_at=ends_at,
        )
        self._store.save(delegation)
        return delegation

    def revoke(self, firm_id: str, delegation_id: str) -> Delegation:
        delegation = self._store.get(firm_id, delegation_id)
        if delegation is None:
            raise KeyError(delegation_id)
        delegation.revoked = True
        self._store.save(delegation)
        return delegation

    def active_delegations_for(
        self, firm_id: str, delegate_id: str, now: datetime | None = None
    ) -> list[Delegation]:
        now = now if now is not None else datetime.now(UTC)
        return [
            d
            for d in self._store.list_for_delegate(firm_id, delegate_id)
            if not d.revoked and d.starts_at <= now <= d.ends_at
        ]

    def has_delegated_permission(
        self, firm_id: str, delegate_id: str, permission: Permission, now: datetime | None = None
    ) -> bool:
        return any(
            permission in d.permissions
            for d in self.active_delegations_for(firm_id, delegate_id, now)
        )

    def active_delegations_for_firm(
        self, firm_id: str, now: datetime | None = None
    ) -> list[Delegation]:
        now = now if now is not None else datetime.now(UTC)
        return [
            d
            for d in self._store.list_for_firm(firm_id)
            if not d.revoked and d.starts_at <= now <= d.ends_at
        ]
