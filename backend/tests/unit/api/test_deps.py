import uuid

import pytest
from fastapi import HTTPException

from tmis.api.deps import Principal, require_role, require_scope


def _principal(role: str = "lawyer", scopes: frozenset[str] = frozenset()) -> Principal:
    return Principal(user_id=uuid.uuid4(), firm_id=uuid.uuid4(), role=role, scopes=scopes)


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
