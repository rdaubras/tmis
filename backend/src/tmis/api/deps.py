"""Shared FastAPI dependencies for authentication & authorization.

`get_current_principal` is the one place a request's JWT gets decoded and
turned into a `Principal`. It is wired as a router-level dependency on
every protected route (see `tmis.api.v1.router`, ADR-SEC-02: default-deny)
rather than opted into per-route, so a new route is authenticated by
default without its author having to remember to add anything.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tmis.core.security import TokenError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)

# Every failure below — missing header, bad signature, expired token,
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


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail=_UNAUTHENTICATED_DETAIL)
    try:
        claims = decode_access_token(credentials.credentials)
        return Principal(
            user_id=uuid.UUID(str(claims["sub"])),
            firm_id=uuid.UUID(str(claims["firm_id"])),
            role=str(claims.get("role", "")),
            scopes=frozenset(claims.get("scopes", [])),
        )
    except (TokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=_UNAUTHENTICATED_DETAIL) from exc


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
