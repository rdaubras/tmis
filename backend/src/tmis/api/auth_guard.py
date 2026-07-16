"""App-level authentication guard (ADR-SEC-03, docs/07-strategie-securite.md).

ADR-SEC-02's default-deny was wired as a dependency on `protected_router`
(`tmis.api.v1.router`), so any router mounted directly on `app` instead —
as `platform`, `cloud_operations` and `runtime_platform` were — silently
skipped it. Enforcement now lives here, one layer up, as an app-level
middleware: it runs for *every* request regardless of which router
handles it or where that router is mounted, so the mount point can no
longer create a hole. `PUBLIC_PATHS` (built by `build_public_paths`) is
the one inventory of routes reachable with no token; anything else
requires `Authorization: Bearer <access_token>`.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from tmis.api.deps import _UNAUTHENTICATED_DETAIL, principal_from_claims
from tmis.core.security import TokenError, decode_access_token


def build_public_paths(api_v1_prefix: str) -> frozenset[str]:
    """The single, auditable inventory of routes reachable with no
    token. A route absent from here requires a valid access token no
    matter which router it lives on or where that router is mounted."""
    return frozenset(
        {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            f"{api_v1_prefix}/health",
            f"{api_v1_prefix}/auth/login",
            f"{api_v1_prefix}/auth/refresh",
            "/platform/health/live",  # sonde liveness k8s
            "/platform/health/ready",  # sonde readiness k8s
        }
    )


class AuthenticationGuardMiddleware:
    """Decodes the bearer token once per request and stashes the
    resulting `Principal` on `request.state.principal`; route handlers
    that need it read it back through `tmis.api.deps.get_current_principal`
    instead of re-decoding — one decode, one source of truth per request.
    """

    def __init__(self, public_paths: frozenset[str]) -> None:
        self._public = public_paths

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # CORS preflight never carries a token — let it through, or the
        # browser can't even ask whether the real request is allowed.
        if request.method == "OPTIONS" or request.url.path in self._public:
            return await call_next(request)

        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse({"detail": _UNAUTHENTICATED_DETAIL}, status_code=401)
        try:
            request.state.principal = principal_from_claims(decode_access_token(token))
        except (TokenError, KeyError, ValueError):
            return JSONResponse({"detail": _UNAUTHENTICATED_DETAIL}, status_code=401)
        return await call_next(request)
