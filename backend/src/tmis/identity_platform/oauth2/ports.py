from typing import Protocol

from tmis.identity_platform.oauth2.schemas import AuthorizationCodeRecord, OAuth2Client


class OAuth2ClientStorePort(Protocol):
    def save(self, client: OAuth2Client) -> None: ...

    def get(self, client_id: str) -> OAuth2Client | None: ...


class AuthorizationCodeStorePort(Protocol):
    def save(self, record: AuthorizationCodeRecord) -> None: ...

    def get(self, code: str) -> AuthorizationCodeRecord | None: ...
