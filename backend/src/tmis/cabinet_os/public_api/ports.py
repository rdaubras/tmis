from typing import Protocol

from tmis.cabinet_os.public_api.schemas import (
    ApiKey,
    ApiScope,
    OAuthClient,
    OAuthToken,
    RateLimitResult,
)


class ApiKeyStorePort(Protocol):
    def get(self, key_id: str) -> ApiKey | None: ...

    def get_by_hash(self, key_hash: str) -> ApiKey | None: ...

    def save(self, key: ApiKey) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[ApiKey]: ...


class OAuthClientStorePort(Protocol):
    def get_by_client_id(self, client_id: str) -> OAuthClient | None: ...

    def save(self, client: OAuthClient) -> None: ...


class OAuthTokenStorePort(Protocol):
    def save(self, token: OAuthToken) -> None: ...

    def get(self, token: str) -> OAuthToken | None: ...


class RateLimiterPort(Protocol):
    """Extension point for a real distributed rate limiter (Redis
    token bucket, ...) — see docs/44-guide-api-publique.md."""

    def check(self, identity: str) -> RateLimitResult: ...


class PublicApiEnginePort(Protocol):
    """Port implemented by every interchangeable public API engine."""

    def issue_api_key(
        self, firm_id: str, name: str, scopes: frozenset[ApiScope]
    ) -> tuple[ApiKey, str]: ...

    def revoke_api_key(self, key_id: str) -> ApiKey: ...

    def authenticate_api_key(self, raw_key: str) -> ApiKey | None: ...

    def list_api_keys(self, firm_id: str) -> list[ApiKey]: ...

    def register_oauth_client(
        self, firm_id: str, redirect_uris: list[str], scopes: frozenset[ApiScope]
    ) -> tuple[OAuthClient, str]: ...

    def issue_oauth_token(self, client_id: str, client_secret: str) -> OAuthToken: ...

    def authenticate_oauth_token(self, token: str) -> OAuthToken | None: ...

    def check_rate_limit(self, identity: str) -> RateLimitResult: ...

    def has_scope(self, granted: frozenset[ApiScope], required: ApiScope) -> bool: ...
