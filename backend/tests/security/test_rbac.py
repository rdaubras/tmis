"""DoD item 6: a caller with the wrong role gets 403 on a
`require_role`-guarded route (T6) — demonstrated on
`identity-platform/dashboard`, deliberately left with zero checks
before this sprint."""

from collections.abc import Callable
from typing import Any

from tmis.domain.identity.value_objects import Role


def test_collaborator_role_is_rejected_from_admin_dashboard(
    authenticated_session: Callable[..., Any],
) -> None:
    session = authenticated_session(role=Role.COLLABORATOR)

    response = session.client.get(
        "/api/v1/identity-platform/dashboard",
        params={"firm_id": str(session.user.firm_id)},
    )

    assert response.status_code == 403


def test_lawyer_role_is_rejected_from_security_events(
    authenticated_session: Callable[..., Any],
) -> None:
    session = authenticated_session(role=Role.LAWYER)

    response = session.client.get(
        "/api/v1/identity-platform/security-events",
        params={"firm_id": str(session.user.firm_id)},
    )

    assert response.status_code == 403


def test_firm_admin_role_is_allowed_on_admin_dashboard(
    authenticated_session: Callable[..., Any],
) -> None:
    session = authenticated_session(role=Role.FIRM_ADMIN)

    response = session.client.get(
        "/api/v1/identity-platform/dashboard",
        params={"firm_id": str(session.user.firm_id)},
    )

    assert response.status_code == 200
