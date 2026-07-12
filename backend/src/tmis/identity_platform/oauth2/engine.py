import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from tmis.core.security import create_access_token
from tmis.identity_platform.oauth2.ports import AuthorizationCodeStorePort, OAuth2ClientStorePort
from tmis.identity_platform.oauth2.schemas import (
    AuthorizationCodeRecord,
    OAuth2Client,
    OAuth2Error,
    TokenPair,
    new_authorization_code_expiry,
    new_client_id,
)


def _hash_client_secret(secret: str) -> str:
    """SHA-256, not bcrypt: a client secret is an opaque, high-entropy
    generated token, never a user-chosen password — same rationale
    already documented by `cabinet_os.public_api.security.hash_secret`
    for API keys/OAuth client secrets. Reimplemented locally rather
    than importing across the dependency direction (`identity_platform`
    is the foundation every other bounded context depends on, never
    the reverse)."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class OAuth2Engine:
    """Authorization Code grant — user-interactive login into TMIS
    itself. Distinct from `cabinet_os.public_api.OAuthClient` (Sprint
    9), which implements the Client Credentials grant for
    machine-to-machine access to the public API — two OAuth2 grant
    types, two different scopes, never confused. Reuses
    `tmis.core.security.create_access_token` directly for JWT
    issuance rather than reimplementing it."""

    def __init__(
        self, client_store: OAuth2ClientStorePort, code_store: AuthorizationCodeStorePort
    ) -> None:
        self._clients = client_store
        self._codes = code_store

    def register_client(
        self, firm_id: str, redirect_uris: tuple[str, ...]
    ) -> tuple[OAuth2Client, str]:
        secret = secrets.token_urlsafe(32)
        client = OAuth2Client(
            client_id=new_client_id(),
            firm_id=firm_id,
            redirect_uris=redirect_uris,
            client_secret_hash=_hash_client_secret(secret),
        )
        self._clients.save(client)
        return client, secret

    def issue_authorization_code(
        self, client_id: str, user_id: str, firm_id: str, redirect_uri: str
    ) -> str:
        client = self._clients.get(client_id)
        if client is None or redirect_uri not in client.redirect_uris:
            raise OAuth2Error("invalid_client_or_redirect_uri")
        code = secrets.token_urlsafe(24)
        self._codes.save(
            AuthorizationCodeRecord(
                code=code,
                client_id=client_id,
                user_id=user_id,
                firm_id=firm_id,
                redirect_uri=redirect_uri,
                expires_at=new_authorization_code_expiry(),
            )
        )
        return code

    def exchange_code(
        self, client_id: str, client_secret: str, code: str, redirect_uri: str
    ) -> TokenPair:
        client = self._clients.get(client_id)
        if client is None or not hmac.compare_digest(
            _hash_client_secret(client_secret), client.client_secret_hash
        ):
            raise OAuth2Error("invalid_client")

        record = self._codes.get(code)
        if (
            record is None
            or record.used
            or record.client_id != client_id
            or record.redirect_uri != redirect_uri
            or record.expires_at < datetime.now(UTC)
        ):
            raise OAuth2Error("invalid_grant")

        record.used = True
        access_token = create_access_token(record.user_id, {"firm_id": record.firm_id})
        refresh_token = secrets.token_urlsafe(32)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=record.user_id,
            firm_id=record.firm_id,
        )
