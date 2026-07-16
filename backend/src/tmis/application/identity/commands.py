"""Login/refresh use cases for the `identity` bounded context (ADR-SEC-01:
`domain/identity` + `SqlAlchemyUserRepository` is the sole authentication
source of truth for this sprint — see docs/07-strategie-securite.md)."""

import uuid
from dataclasses import dataclass

from tmis.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from tmis.domain.identity.entities import User
from tmis.domain.identity.ports import UserRepositoryPort
from tmis.domain.identity.value_objects import Email

# A precomputed hash so `verify_password` always runs a real bcrypt
# comparison, even when the email doesn't match any user — otherwise an
# unknown-email login would return faster than a wrong-password one,
# leaking which emails are registered through response timing.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password-used-for-timing-safety-only")


class InvalidCredentialsError(Exception):
    """Raised for unknown email, wrong password, inactive account, or an
    invalid/expired refresh token. Deliberately one exception type for
    all of these — the API layer maps it to a single generic 401 so a
    caller can never distinguish "no such account" from "wrong
    password" (no account-enumeration signal)."""


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RefreshCommand:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


def _claims_for(user: User) -> dict[str, object]:
    return {
        "firm_id": str(user.firm_id),
        "role": user.role.value,
        "scopes": [permission.value for permission in user.permissions],
    }


def _issue_tokens(user: User) -> AuthResult:
    claims = _claims_for(user)
    return AuthResult(
        user=user,
        access_token=create_access_token(str(user.id), claims),
        refresh_token=create_refresh_token(str(user.id), claims),
    )


class LoginUseCase:
    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._users = user_repository

    def execute(self, command: LoginCommand) -> AuthResult:
        try:
            email = Email(command.email)
        except ValueError as exc:
            raise InvalidCredentialsError("invalid credentials") from exc

        user = self._users.get_by_email(email)
        password_hash = user.hashed_password if user is not None else _DUMMY_PASSWORD_HASH
        password_matches = verify_password(command.password, password_hash)

        if user is None or not user.is_active or not password_matches:
            raise InvalidCredentialsError("invalid credentials")

        return _issue_tokens(user)


class RefreshUseCase:
    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._users = user_repository

    def execute(self, command: RefreshCommand) -> AuthResult:
        try:
            claims = decode_refresh_token(command.refresh_token)
            user_id = uuid.UUID(str(claims["sub"]))
            firm_id = uuid.UUID(str(claims["firm_id"]))
        except (TokenError, KeyError, ValueError) as exc:
            raise InvalidCredentialsError("invalid refresh token") from exc

        # Reload from the repository rather than trust the old claims —
        # picks up role changes and deactivation since the token was
        # issued, and rotates the refresh token on every use.
        user = self._users.get_by_id(user_id, firm_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("invalid refresh token")

        return _issue_tokens(user)
