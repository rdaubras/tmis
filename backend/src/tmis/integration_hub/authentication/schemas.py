from dataclasses import dataclass, field
from enum import StrEnum


class AuthMethod(StrEnum):
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    API_KEY = "api_key"
    JWT = "jwt"
    CERTIFICATE = "certificate"


@dataclass(frozen=True, slots=True)
class AuthCredentials:
    """Opaque per-method credential bag — "le choix du mécanisme
    dépend du système cible" (sprint requirement): the caller picks
    `method`, `values` holds whatever that method needs (client
    id/secret, token, key, certificate fingerprint...)."""

    method: AuthMethod
    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuthResult:
    authenticated: bool
    detail: str = ""
