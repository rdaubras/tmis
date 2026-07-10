from collections.abc import Awaitable, Callable

from fastapi import Request, Response

_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)
_HSTS_MAX_AGE_SECONDS = 63_072_000  # two years, includeSubDomains + preload eligible


class SecurityHeadersMiddleware:
    """Adds the security headers every response should carry (see
    docs/47-guide-securite-entreprise.md): Content-Security-Policy,
    Strict-Transport-Security (HSTS), `X-Content-Type-Options`,
    `X-Frame-Options`, and `Referrer-Policy`. Configurable so a
    deployment can tighten the CSP further without touching call
    sites — this is middleware, not a scattered set of per-route
    headers."""

    def __init__(
        self,
        content_security_policy: str = _DEFAULT_CSP,
        hsts_max_age_seconds: int = _HSTS_MAX_AGE_SECONDS,
        enable_hsts: bool = True,
    ) -> None:
        self._csp = content_security_policy
        self._hsts_max_age_seconds = hsts_max_age_seconds
        self._enable_hsts = enable_hsts

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = self._csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if self._enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self._hsts_max_age_seconds}; includeSubDomains; preload"
            )
        return response


CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type", "X-Trace-Id", "X-CSRF-Token"]


def validate_cors_origins(allowed_origins: list[str]) -> list[str]:
    """Rejects a wildcard CORS origin: combined with
    `allow_credentials=True` (required for bearer-token auth from a
    browser) it is a misconfiguration the browser spec forbids and
    FastAPI would otherwise accept silently. Returns the origins
    unchanged so this can be called inline where `CORSMiddleware` is
    configured."""
    if "*" in allowed_origins:
        raise ValueError(
            "Wildcard CORS origin is not allowed alongside allow_credentials=True; "
            "list explicit origins instead."
        )
    return allowed_origins
