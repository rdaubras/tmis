"""Shared FastAPI dependencies for authentication & authorization.

Token verification happens once per request, at the application boundary,
in `tmis.api.auth_guard.AuthenticationGuardMiddleware` (ADR-SEC-03: the
guard runs for every request regardless of which router handles it or
where that router is mounted, so a route can no longer escape enforcement
by being mounted outside `protected_router`). `get_current_principal`
below is a *reader*, not a decoder: it hands route handlers the
`Principal` the guard already stashed on `request.state.principal`, and
fails closed (401) if that state is missing — reachable only if a route
somehow bypassed the guard, or a test calls the dependency directly.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

# Every auth failure — missing header, bad signature, expired token,
# malformed claims — surfaces as this one generic 401. Never a 500, and
# never a message that discloses which of those it was (see
# docs/07-strategie-securite.md).
_UNAUTHENTICATED_DETAIL = "Authentification requise."


@dataclass(frozen=True, slots=True)
class Principal:
    """The authenticated caller's identity, resolved once per request
    straight from the validated access token — never from a
    client-supplied header (see `get_current_firm_id`)."""

    user_id: uuid.UUID
    firm_id: uuid.UUID
    role: str
    scopes: frozenset[str] = field(default_factory=frozenset)


def principal_from_claims(claims: dict[str, Any]) -> Principal:
    return Principal(
        user_id=uuid.UUID(str(claims["sub"])),
        firm_id=uuid.UUID(str(claims["firm_id"])),
        role=str(claims.get("role", "")),
        scopes=frozenset(claims.get("scopes", [])),
    )


def get_current_principal(request: Request) -> Principal:
    principal: Principal | None = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=401, detail=_UNAUTHENTICATED_DETAIL)
    return principal


def get_current_firm_id(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> uuid.UUID:
    """Tenant resolution from the authenticated token — the only source
    of `firm_id` for any route. Replaces the earlier `X-Firm-Id` header
    (see docs/07-strategie-securite.md — isolation multi-tenant): a
    client can no longer claim a tenant, it can only be handed one by
    the auth server via a signed access token.
    """
    return principal.firm_id


def require_role(*roles: str) -> Callable[..., Principal]:
    """Returns a dependency callable — use as `Depends(require_role(...))`,
    either in a route's `dependencies=` list or as a parameter default
    when the route body also needs the `Principal`."""

    def _check(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Rôle insuffisant.")
        return principal

    return _check


def require_scope(*scopes: str) -> Callable[..., Principal]:
    """Returns a dependency callable — use as `Depends(require_scope(...))`."""

    def _check(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        if not set(scopes).issubset(principal.scopes):
            raise HTTPException(status_code=403, detail="Permission insuffisante.")
        return principal

    return _check
