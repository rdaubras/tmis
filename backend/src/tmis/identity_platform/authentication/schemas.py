from dataclasses import dataclass, field
from enum import StrEnum


class AuthMethod(StrEnum):
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openid_connect"
    PASSWORDLESS = "passwordless"
    MAGIC_LINK = "magic_link"
    WEBAUTHN = "webauthn"


@dataclass(frozen=True, slots=True)
class AuthCredentials:
    method: AuthMethod
    firm_id: str
    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuthResult:
    authenticated: bool
    user_id: str = ""
    detail: str = ""
