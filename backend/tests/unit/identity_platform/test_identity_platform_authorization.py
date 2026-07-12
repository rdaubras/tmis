from tmis.identity_platform.abac.engine import AbacEngine
from tmis.identity_platform.abac.rules import (
    ConfidentialityRule,
    MinimumSeniorityRule,
    SameDepartmentRule,
)
from tmis.identity_platform.abac.schemas import AbacAttributes
from tmis.identity_platform.authorization.engine import AuthorizationEngine
from tmis.identity_platform.identity_context.schemas import IdentityContext
from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.policy_engine.engine import PolicyEngine
from tmis.identity_platform.policy_engine.store import InMemoryPolicyStore
from tmis.identity_platform.rbac.engine import RbacEngine
from tmis.identity_platform.roles.engine import RoleEngine
from tmis.identity_platform.roles.schemas import Role
from tmis.identity_platform.roles.store import InMemoryRoleAssignmentStore

_EXPERIENCE_RANK = {"junior": 0, "senior": 1, "partner": 2}


def _authorization_engine() -> tuple[AuthorizationEngine, RoleEngine, PolicyEngine]:
    roles = RoleEngine(InMemoryRoleAssignmentStore())
    rbac = RbacEngine()
    abac = AbacEngine(
        [
            MinimumSeniorityRule(min_years=0),
            ConfidentialityRule(_EXPERIENCE_RANK),
            SameDepartmentRule(),
        ]
    )
    policies = PolicyEngine(InMemoryPolicyStore())
    return AuthorizationEngine(roles, rbac, abac, policies), roles, policies


def _identity(**overrides: object) -> IdentityContext:
    base = {
        "user_id": "user-1",
        "firm_id": "firm-1",
        "experience_level": "partner",
        "seniority_years": 10,
    }
    base.update(overrides)
    return IdentityContext(**base)  # type: ignore[arg-type]


def test_rbac_denies_when_role_lacks_permission() -> None:
    authorization, roles, _policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARALEGAL)

    decision = authorization.check(_identity(), Permission.CONSULTATION_VALIDATE)

    assert decision.allowed is False
    assert "aucun rôle" in decision.reason


def test_rbac_allows_partner_to_validate_consultation() -> None:
    authorization, roles, _policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)

    decision = authorization.check(_identity(), Permission.CONSULTATION_VALIDATE)

    assert decision.allowed is True


def test_abac_denies_junior_on_privileged_confidentiality_even_with_role() -> None:
    authorization, roles, _policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)
    identity = _identity(experience_level="junior")

    decision = authorization.check(
        identity,
        Permission.CONSULTATION_VALIDATE,
        AbacAttributes(confidentiality_level="privileged"),
    )

    assert decision.allowed is False
    assert "ABAC" in decision.reason


def test_abac_denies_cross_department_access() -> None:
    authorization, roles, _policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)
    identity = _identity(department_id="dept-a")

    decision = authorization.check(
        identity, Permission.CONSULTATION_VALIDATE, AbacAttributes(department_id="dept-b")
    )

    assert decision.allowed is False


def test_policy_can_deny_what_rbac_already_granted() -> None:
    authorization, roles, policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)
    policies.create("firm-1", Permission.EXPORT_DATA, denied_roles=frozenset({Role.PARTNER}))

    decision = authorization.check(_identity(), Permission.EXPORT_DATA)

    assert decision.allowed is False


def test_policy_can_require_second_validation() -> None:
    authorization, roles, policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)
    policies.create("firm-1", Permission.STRATEGY_DRAFT_VALIDATE, requires_second_validation=True)

    decision = authorization.check(_identity(), Permission.STRATEGY_DRAFT_VALIDATE)

    assert decision.allowed is True
    assert decision.requires_second_validation is True


def test_policy_can_restrict_permission_to_a_team() -> None:
    authorization, roles, policies = _authorization_engine()
    roles.assign("firm-1", "user-1", Role.PARTNER)
    policies.create(
        "firm-1", Permission.WORKFLOW_USE_TEAM_RESTRICTED, restricted_to_team_id="team-x"
    )

    denied = authorization.check(
        _identity(team_id="team-y"), Permission.WORKFLOW_USE_TEAM_RESTRICTED
    )
    allowed = authorization.check(
        _identity(team_id="team-x"), Permission.WORKFLOW_USE_TEAM_RESTRICTED
    )

    assert denied.allowed is False
    assert allowed.allowed is True


def test_zero_trust_check_never_implicitly_allows_unknown_identity() -> None:
    """No role assigned, no policy configured: `check()` still must
    return an explicit deny, never an implicit allow — the sprint's
    Zero Trust constraint ("aucun accès implicite")."""
    authorization, _roles, _policies = _authorization_engine()

    decision = authorization.check(_identity(user_id="ghost"), Permission.EXPORT_DATA)

    assert decision.allowed is False
