from tmis.identity_platform.abac.engine import AbacEngine
from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.authorization.schemas import AuthorizationDecision
from tmis.identity_platform.identity_context.schemas import IdentityContext
from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.rbac.engine import RbacEngine
from tmis.identity_platform.roles.engine import RoleEngine


class AuthorizationEngine:
    """The single, central authorization entry point every module of
    TMIS is meant to call — "toutes les autorisations passent par le
    moteur central" (sprint constraint). Combines three layers in
    order, each able to deny what the previous one allowed, never the
    reverse: RBAC baseline → ABAC conditions → firm-specific
    `Policy` overrides (which may also require a second validation).
    Zero Trust: `check()` never returns an implicit allow — every
    caller must inspect `AuthorizationDecision.allowed` explicitly."""

    def __init__(
        self,
        role_engine: RoleEngine,
        rbac_engine: RbacEngine,
        abac_engine: AbacEngine,
        policy_engine: PolicyEngine,
    ) -> None:
        self._roles = role_engine
        self._rbac = rbac_engine
        self._abac = abac_engine
        self._policies = policy_engine

    def check(
        self,
        identity: IdentityContext,
        permission: Permission,
        attributes: AbacAttributes | None = None,
    ) -> AuthorizationDecision:
        attributes = attributes if attributes is not None else AbacAttributes()
        roles = tuple(self._roles.roles_for_user(identity.firm_id, identity.user_id))

        if not self._rbac.has_permission(roles, permission):
            return AuthorizationDecision(
                allowed=False,
                reason=f"aucun rôle de {identity.user_id!r} n'accorde {permission.value}",
            )

        if not self._abac.evaluate(identity, attributes):
            return AuthorizationDecision(
                allowed=False, reason="condition d'accès contextuelle (ABAC) non satisfaite"
            )

        policy_decision = self._policies.evaluate(
            identity.firm_id, permission, roles, team_id=identity.team_id
        )
        if not policy_decision.allowed:
            return AuthorizationDecision(allowed=False, reason=policy_decision.reason)

        return AuthorizationDecision(
            allowed=True, requires_second_validation=policy_decision.requires_second_validation
        )
