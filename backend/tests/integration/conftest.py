"""Legacy test support for the security sprint's default-deny change
(ADR-SEC-02, see docs/07-strategie-securite.md).

Every integration test in this tree built its own `TestClient(app)`
before every route under `/api/v1` required a valid access token. Rather
than bypass authentication for them via `dependency_overrides` — which
would stop exercising the real auth path — this autouse fixture patches
`TestClient` to carry a real, validly signed access token by default.
The full decode/signature/claims path in `tmis.core.security` and
`tmis.api.deps.get_current_principal` still runs on every request;
nothing about auth itself is skipped, only supplied automatically so
tests that predate auth and aren't about auth don't all have to be
rewritten to mint their own token.

Tests that ARE about auth belong in `tests/security/`, which does not
import this fixture and talks to `TestClient(app)` with no default
token at all.
"""

import uuid
from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient as _TestClient

from tmis.core.security import create_access_token
from tmis.domain.identity.value_objects import DEFAULT_ROLE_PERMISSIONS, Role

_DEFAULT_TEST_FIRM_ID = uuid.uuid4()
_DEFAULT_TEST_USER_ID = uuid.uuid4()


def _default_test_token() -> str:
    return create_access_token(
        str(_DEFAULT_TEST_USER_ID),
        {
            "firm_id": str(_DEFAULT_TEST_FIRM_ID),
            "role": Role.PLATFORM_ADMIN.value,
            "scopes": [p.value for p in DEFAULT_ROLE_PERMISSIONS[Role.PLATFORM_ADMIN]],
        },
    )


@pytest.fixture(autouse=True)
def _default_bearer_token(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    token = _default_test_token()
    original_init = _TestClient.__init__

    def _patched_init(self: _TestClient, *args: object, **kwargs: object) -> None:
        headers = dict(kwargs.pop("headers", None) or {})  # type: ignore[arg-type]
        headers.setdefault("Authorization", f"Bearer {token}")
        original_init(self, *args, headers=headers, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_TestClient, "__init__", _patched_init)
    yield
