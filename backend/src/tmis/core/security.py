import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from tmis.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


class TokenError(JWTError):
    """Raised for any invalid, expired, malformed, or wrong-type token.

    Subclasses `jose.JWTError` so existing `except JWTError` call sites
    (magic links, OAuth2, OIDC — all built on `create_access_token`)
    keep working unchanged, while new call sites can catch this more
    specific type. Never carries the underlying cause in its message —
    callers surface a generic 401, never the decode failure detail.
    """


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    claims: dict[str, Any] | None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        # Unique per token so two tokens minted in the same second for
        # the same subject/claims (e.g. back-to-back refreshes) are
        # still distinct values — needed for refresh rotation to mean
        # anything, and useful later for a revocation list.
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": token_type,
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    return _create_token(
        subject, "access", timedelta(minutes=settings.access_token_expire_minutes), claims
    )


def create_refresh_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    return _create_token(
        subject, "refresh", timedelta(days=settings.refresh_token_expire_days), claims
    )


def _decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            # Algorithms come only from server-side settings, never from
            # the token's own header — blocks both `alg=none` and
            # algorithm-confusion attacks.
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except JWTError as exc:
        raise TokenError("invalid token") from exc
    if payload.get("token_type") != expected_type:
        raise TokenError(f"expected a {expected_type} token")
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    return _decode_token(token, "refresh")
