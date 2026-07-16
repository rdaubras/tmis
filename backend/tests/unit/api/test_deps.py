import uuid

import pytest
from fastapi import HTTPException, Request

from tmis.api.deps import (
    Principal,
    get_current_principal,
    principal_from_claims,
    require_role,
    require_scope,
)


def _principal(role: str = "lawyer", scopes: frozenset[str] = frozenset()) -> Principal:
    return Principal(user_id=uuid.uuid4(), firm_id=uuid.uuid4(), role=role, scopes=scopes)


def _request_with_state(**state: object) -> Request:
    """A `Request` is normally built by the ASGI server; here we only
    need something whose `.state` carries whatever the auth guard would
    have stashed on it, which is all `get_current_principal` reads."""
    request = Request(scope={"type": "http"})
    request.scope["state"] = state
    return request


def test_get_current_principal_reads_the_principal_the_guard_stashed() -> None:
    principal = _principal()
    request = _request_with_state(principal=principal)
    assert get_current_principal(request) is principal


def test_get_current_principal_fails_closed_when_the_guard_never_ran() -> None:
    """Reachable only if a route somehow bypassed
    `AuthenticationGuardMiddleware`, or a test calls the dependency
    directly without going through it — either way, fail closed."""
    request = _request_with_state()
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(request)
    assert exc_info.value.status_code == 401


def test_principal_from_claims_builds_a_principal_from_decoded_jwt_claims() -> None:
    user_id = uuid.uuid4()
    firm_id = uuid.uuid4()
    claims = {
        "sub": str(user_id),
        "firm_id": str(firm_id),
        "role": "lawyer",
        "scopes": ["case:read"],
    }
    principal = principal_from_claims(claims)
    assert principal == Principal(
        user_id=user_id, firm_id=firm_id, role="lawyer", scopes=frozenset({"case:read"})
    )


def test_require_role_allows_a_matching_role() -> None:
    check = require_role("firm_admin", "platform_admin")
    principal = _principal(role="firm_admin")
    assert check(principal) is principal


def test_require_role_rejects_a_non_matching_role() -> None:
    check = require_role("firm_admin", "platform_admin")
    with pytest.raises(HTTPException) as exc_info:
        check(_principal(role="lawyer"))
    assert exc_info.value.status_code == 403


def test_require_scope_allows_when_all_scopes_present() -> None:
    check = require_scope("case:read", "case:write")
    principal = _principal(scopes=frozenset({"case:read", "case:write", "document:read"}))
    assert check(principal) is principal


def test_require_scope_rejects_when_a_scope_is_missing() -> None:
    check = require_scope("case:read", "firm:manage")
    with pytest.raises(HTTPException) as exc_info:
        check(_principal(scopes=frozenset({"case:read"})))
    assert exc_info.value.status_code == 403
