from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.ports import PolicyStorePort
from tmis.identity_platform.policy_engine.schemas import (
    Policy,
    PolicyDecision,
    PolicyEffect,
    new_policy_id,
)
from tmis.identity_platform.roles.schemas import Role


class PolicyEngine:
    """The sprint's central policy engine — "toutes les politiques
    sont configurables". Layered *on top of* `rbac.RbacEngine`: a
    permission already granted by role can still be denied, scoped to
    a team, or made to require a second validation by a firm-specific
    `Policy`."""

    def __init__(self, store: PolicyStorePort) -> None:
        self._store = store

    def create(
        self,
        firm_id: str,
        permission: Permission,
        *,
        effect: PolicyEffect = PolicyEffect.DENY,
        allowed_roles: frozenset[Role] = frozenset(),
        denied_roles: frozenset[Role] = frozenset(),
        restricted_to_team_id: str | None = None,
        requires_second_validation: bool = False,
        reason: str = "",
    ) -> Policy:
        policy = Policy(
            id=new_policy_id(),
            firm_id=firm_id,
            permission=permission,
            effect=effect,
            allowed_roles=allowed_roles,
            denied_roles=denied_roles,
            restricted_to_team_id=restricted_to_team_id,
            requires_second_validation=requires_second_validation,
            reason=reason,
        )
        self._store.save(policy)
        return policy

    def evaluate(
        self,
        firm_id: str,
        permission: Permission,
        roles: tuple[Role, ...],
        team_id: str | None = None,
    ) -> PolicyDecision:
        requires_second_validation = False
        for policy in self._store.list_for_permission(firm_id, permission):
            if policy.denied_roles and any(r in policy.denied_roles for r in roles):
                return PolicyDecision(
                    allowed=False, reason=policy.reason or f"rôle refusé pour {permission.value}"
                )
            if policy.allowed_roles and not any(r in policy.allowed_roles for r in roles):
                return PolicyDecision(
                    allowed=False,
                    reason=policy.reason or f"rôle non autorisé pour {permission.value}",
                )
            if policy.restricted_to_team_id is not None and policy.restricted_to_team_id != team_id:
                return PolicyDecision(
                    allowed=False, reason=policy.reason or "réservé à une équipe spécifique"
                )
            if policy.requires_second_validation:
                requires_second_validation = True
        return PolicyDecision(allowed=True, requires_second_validation=requires_second_validation)

    def list_active_for_firm(self, firm_id: str) -> list[Policy]:
        return [p for p in self._store.list_for_firm(firm_id) if p.active]
