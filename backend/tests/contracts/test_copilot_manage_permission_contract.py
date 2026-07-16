"""Contract test for the RBAC permission `Permission.COPILOT_MANAGE`
(`tmis.identity_platform.permissions.schemas`), the permission every
mutating `legal_copilot_framework` endpoint gates on via
`identity_platform.api.guard.authorize_or_403`.

Sprint 43's Phase 0 audit found that the exact "Sprint 24 → Sprint 25"
narrative in the sprint brief does not match this repo's history: git
history and `docs/reports/sprint-24-rapport-architecture.md` show
`COPILOT_MANAGE` was granted to no role only transiently, caught and
fixed *within* Sprint 24 itself before that sprint's commit — it never
shipped broken, and Sprint 25 never touched this permission. See
docs/reports/sprint-43-rapport-audit.md for the corrected narrative.

This suite still adds the regression-prevention contract test the
brief asked for: an ungranted `COPILOT_MANAGE` is exactly the kind of
cross-context (identity_platform ↔ legal_copilot_framework) silent
failure this sprint's `tests/contracts/` exists to catch, whatever
sprint the near-miss belongs to.
"""

from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.rbac.engine import RbacEngine
from tmis.identity_platform.rbac.schemas import DEFAULT_ROLE_PERMISSIONS
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app

_FIRM = "firm-contract-copilot"


def test_a_matrix_without_copilot_manage_reproduces_the_historical_near_miss() -> None:
    """Regression-first: reproduce the exact failure mode the brief
    describes (a role/permission matrix with `COPILOT_MANAGE` granted to
    no role) and confirm `RbacEngine.has_permission` correctly reports it
    as denied — proving this suite would have caught it, had it existed
    at the time."""
    matrix_missing_copilot_manage = {
        role: frozenset(p for p in permissions if p is not Permission.COPILOT_MANAGE)
        for role, permissions in DEFAULT_ROLE_PERMISSIONS.items()
    }
    engine = RbacEngine(matrix_missing_copilot_manage)

    assert engine.has_permission((Role.PARTNER,), Permission.COPILOT_MANAGE) is False
    assert engine.has_permission((Role.IT_ADMIN,), Permission.COPILOT_MANAGE) is False


def test_copilot_manage_is_granted_to_partner_and_it_admin_by_default() -> None:
    """Pins the current, correct state of `DEFAULT_ROLE_PERMISSIONS` so a
    future edit that silently drops the grant for either role fails this
    test instead of waiting for a manual audit."""
    engine = RbacEngine()  # production default: dict(DEFAULT_ROLE_PERMISSIONS)

    assert engine.has_permission((Role.PARTNER,), Permission.COPILOT_MANAGE) is True
    assert engine.has_permission((Role.IT_ADMIN,), Permission.COPILOT_MANAGE) is True


def test_register_copilot_endpoint_authorizes_a_partner_end_to_end() -> None:
    """The real production path, not just the permission matrix: a
    `PARTNER`-assigned user hitting the real
    `POST /api/v1/legal-copilots/register` endpoint through the full
    `RoleEngine` -> `RbacEngine` -> `AuthorizationEngine` ->
    `authorize_or_403` chain must succeed, not 403."""
    get_role_engine().assign(_FIRM, "partner-contract", Role.PARTNER)
    client = TestClient(app)

    response = client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": _FIRM,
            "user_id": "partner-contract",
            "id": "copilot-contract-permission",
            "name": "Copilote contrat",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )

    assert response.status_code == 200
