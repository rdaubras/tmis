import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.public_api.ports import (
    ApiKeyStorePort,
    OAuthClientStorePort,
    OAuthTokenStorePort,
    RateLimiterPort,
)
from tmis.cabinet_os.public_api.schemas import (
    ApiKey,
    ApiScope,
    OAuthClient,
    OAuthToken,
    RateLimitResult,
)
from tmis.cabinet_os.public_api.security import generate_secret, hash_secret, key_prefix

_TOKEN_TTL = timedelta(hours=1)


class PublicApiEngine:
    """Implements `PublicApiEnginePort` (see docs/44-guide-api-publique.md):
    API keys, a client-credentials OAuth2 flow, scope checks and rate
    limiting. Versioning is a routing concern, handled by mounting each
    version's router separately (see `tmis.cabinet_os.api`) rather than
    by this engine."""

    def __init__(
        self,
        api_key_store: ApiKeyStorePort,
        oauth_client_store: OAuthClientStorePort,
        oauth_token_store: OAuthTokenStorePort,
        rate_limiter: RateLimiterPort,
    ) -> None:
        self._api_keys = api_key_store
        self._oauth_clients = oauth_client_store
        self._oauth_tokens = oauth_token_store
        self._rate_limiter = rate_limiter

    def issue_api_key(
        self, firm_id: str, name: str, scopes: frozenset[ApiScope]
    ) -> tuple[ApiKey, str]:
        raw_key = generate_secret()
        key = ApiKey(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            name=name,
            key_hash=hash_secret(raw_key),
            prefix=key_prefix(raw_key),
            scopes=scopes,
            created_at=datetime.now(UTC),
        )
        self._api_keys.save(key)
        return key, raw_key

    def revoke_api_key(self, key_id: str) -> ApiKey:
        key = self._api_keys.get(key_id)
        if key is None:
            raise ValueError(f"Unknown API key {key_id!r}")
        key.revoked_at = datetime.now(UTC)
        self._api_keys.save(key)
        return key

    def authenticate_api_key(self, raw_key: str) -> ApiKey | None:
        key = self._api_keys.get_by_hash(hash_secret(raw_key))
        if key is None or key.revoked_at is not None:
            return None
        key.last_used_at = datetime.now(UTC)
        self._api_keys.save(key)
        return key

    def list_api_keys(self, firm_id: str) -> list[ApiKey]:
        return self._api_keys.list_for_firm(firm_id)

    def register_oauth_client(
        self, firm_id: str, redirect_uris: list[str], scopes: frozenset[ApiScope]
    ) -> tuple[OAuthClient, str]:
        raw_secret = generate_secret()
        client = OAuthClient(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            client_id=str(uuid.uuid4()),
            client_secret_hash=hash_secret(raw_secret),
            redirect_uris=list(redirect_uris),
            scopes=scopes,
            created_at=datetime.now(UTC),
        )
        self._oauth_clients.save(client)
        return client, raw_secret

    def issue_oauth_token(self, client_id: str, client_secret: str) -> OAuthToken:
        client = self._oauth_clients.get_by_client_id(client_id)
        if client is None or client.client_secret_hash != hash_secret(client_secret):
            raise ValueError("Invalid OAuth client credentials")
        now = datetime.now(UTC)
        token = OAuthToken(
            token=generate_secret(),
            client_id=client_id,
            firm_id=client.firm_id,
            scopes=client.scopes,
            issued_at=now,
            expires_at=now + _TOKEN_TTL,
        )
        self._oauth_tokens.save(token)
        return token

    def authenticate_oauth_token(self, token: str) -> OAuthToken | None:
        found = self._oauth_tokens.get(token)
        if found is None or found.expires_at < datetime.now(UTC):
            return None
        return found

    def check_rate_limit(self, identity: str) -> RateLimitResult:
        return self._rate_limiter.check(identity)

    def has_scope(self, granted: frozenset[ApiScope], required: ApiScope) -> bool:
        return required in granted or ApiScope.ADMIN in granted
