import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

_CSRF_COOKIE_NAME = "csrf_token"
_CSRF_HEADER_NAME = "X-CSRF-Token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


class CsrfProtect:
    """Double-submit-cookie CSRF protection (see
    docs/47-guide-securite-entreprise.md — Security). TMIS's API
    primarily authenticates with a JWT bearer token, which is immune to
    classic CSRF (the browser never attaches it automatically) — this
    exists as defense-in-depth for any endpoint or future integration
    that relies on cookies. `verify` is a no-op unless a CSRF cookie is
    actually present, so pure bearer-token clients are unaffected.

    Returns `True`/`False` rather than raising: a `Starlette`
    function-based `@app.middleware("http")` does not run inside the
    framework's exception-handling middleware, so an `HTTPException`
    raised here would propagate as an unhandled 500 instead of a clean
    403 — `csrf_middleware` turns a `False` into a proper `Response`
    itself.
    """

    def verify(self, request: Request) -> bool:
        if request.method not in _UNSAFE_METHODS:
            return True
        cookie_token = request.cookies.get(_CSRF_COOKIE_NAME)
        if cookie_token is None:
            return True
        header_token = request.headers.get(_CSRF_HEADER_NAME)
        if header_token is None or not secrets.compare_digest(cookie_token, header_token):
            return False
        return True


_csrf_protect = CsrfProtect()


async def csrf_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Global middleware wrapping `CsrfProtect` — a no-op for any
    request that carries no CSRF cookie, so bearer-token-only clients
    (TMIS's default) are unaffected."""
    if not _csrf_protect.verify(request):
        return JSONResponse(status_code=403, content={"detail": "CSRF token missing or invalid"})
    return await call_next(request)
