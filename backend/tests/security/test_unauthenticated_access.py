"""DoD item 1: an unauthenticated request to any non-public route is
impossible — not "impossible for the routes we thought to sample", but
verified against `app.routes` itself, so a router mounted anywhere on
`app` (not just through `tmis.api.v1.router.protected_router`) is
automatically covered.

This replaces a hand-maintained sample that shared the same blind spot
as the bug it was meant to catch: `platform`, `cloud_operations` and
`runtime_platform` are mounted directly on `app` (see `main.py`) rather
than through `protected_router`, so a test that only sampled
`protected_router` contexts could never have caught them being
unauthenticated. Enforcement now lives in
`tmis.api.auth_guard.AuthenticationGuardMiddleware` (ADR-SEC-03), which
runs for every request regardless of mount point — this test proves that
by walking the real route table instead of a maintained list.
"""

import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tmis.api.auth_guard import build_public_paths
from tmis.core.config import Settings

_PATH_PARAM_RE = re.compile(r"\{[^{}]+\}")


def _concretize_path_params(path: str) -> str:
    """`{trace_id}` -> `x`. A 401 from the app-level guard precedes any
    routing-level validation of the substituted value, so the
    placeholder never needs to be a value that would actually resolve."""
    return _PATH_PARAM_RE.sub("x", path)


def _iter_non_public_routes(
    app_under_test: FastAPI, public: frozenset[str]
) -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for route in app_under_test.routes:
        path = getattr(route, "path", None)
        methods = (getattr(route, "methods", None) or set()) - {"HEAD", "OPTIONS"}
        if path is None or path in public:
            continue
        concrete = _concretize_path_params(path)
        for method in sorted(methods):
            cases.append((method, concrete))
    return cases


def test_every_non_public_route_requires_auth(
    client_without_token: TestClient, app_under_test: FastAPI, settings: Settings
) -> None:
    public = build_public_paths(settings.api_v1_prefix)
    cases = _iter_non_public_routes(app_under_test, public)
    assert cases, "no non-public route found — the route walk itself is broken"
    for method, path in cases:
        response = client_without_token.request(method, path)
        assert response.status_code == 401, f"{method} {path} -> {response.status_code}"


@pytest.mark.parametrize(
    "path",
    ["/platform/health/live", "/platform/health/ready"],
)
def test_k8s_probes_are_public(client_without_token: TestClient, path: str) -> None:
    response = client_without_token.get(path)
    assert response.status_code != 401, f"GET {path} -> {response.status_code}"


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/platform/monitoring"),
        ("GET", "/cloud-operations/alerts"),
        ("GET", "/cloud-operations/dashboards/overview"),
        ("GET", "/runtime/tasks"),
    ],
)
def test_ops_routes_reject_missing_token_then_accept_a_valid_one(
    client_without_token: TestClient,
    authenticated_session,  # noqa: ANN001 — fixture factory, see conftest
    method: str,
    path: str,
) -> None:
    """The three routers this hotfix closes off (`platform`,
    `cloud_operations`, `runtime_platform`) were previously reachable
    with no token at all. Prove both halves: blocked without one, and
    not simply broken — still served with one."""
    unauthed = client_without_token.request(method, path)
    assert unauthed.status_code == 401, f"{method} {path} -> {unauthed.status_code}"

    session = authenticated_session()
    authed = session.client.request(method, path)
    assert authed.status_code < 400, f"{method} {path} (with token) -> {authed.status_code}"


def test_platform_metrics_stays_protected_by_default(client_without_token: TestClient) -> None:
    """T3: `/platform/metrics` is deliberately *not* in `PUBLIC_PATHS` —
    exposing internal metrics without a token is an explicit, justified
    allowlist entry backed by a NetworkPolicy, never a silent default."""
    response = client_without_token.get("/platform/metrics")
    assert response.status_code == 401


def test_cors_preflight_is_never_blocked_by_the_guard(client_without_token: TestClient) -> None:
    response = client_without_token.options(
        "/api/v1/cases",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code != 401


def test_a_401_from_the_guard_still_carries_cors_headers(client_without_token: TestClient) -> None:
    """The guard must be wrapped by `CORSMiddleware`, not the other way
    around (see the middleware-order comment in `main.py`) — otherwise a
    401 short-circuited by the guard reaches the browser with no
    `Access-Control-Allow-Origin` header, which shows up as an opaque
    CORS error instead of the 401 it actually is."""
    response = client_without_token.get(
        "/api/v1/cases", headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_login_and_refresh_are_public() -> None:
    from tmis.api.v1.router import public_router

    paths = {route.path for route in public_router.routes}  # type: ignore[attr-defined]
    assert "/auth/login" in paths
    assert "/auth/refresh" in paths
