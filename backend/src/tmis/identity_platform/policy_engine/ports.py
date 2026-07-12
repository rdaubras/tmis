from typing import Protocol

from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.schemas import Policy


class PolicyStorePort(Protocol):
    def save(self, policy: Policy) -> None: ...

    def list_for_permission(self, firm_id: str, permission: Permission) -> list[Policy]: ...

    def list_for_firm(self, firm_id: str) -> list[Policy]: ...
