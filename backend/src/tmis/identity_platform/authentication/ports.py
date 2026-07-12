from typing import Protocol

from tmis.identity_platform.authentication.schemas import AuthCredentials, AuthMethod, AuthResult


class AuthStrategyPort(Protocol):
    """One pluggable authentication mechanism — same registry
    extensibility pattern as `integration_hub.authentication.
    AuthStrategyPort` (Sprint 18). Prepared so a future SAML or other
    enterprise IdP strategy can be added by registering a new
    implementation, never by modifying `AuthenticationEngine` — "des
    interfaces permettant d'ajouter ultérieurement des fournisseurs
    SAML... sans dépendance directe" (sprint requirement)."""

    method: AuthMethod

    async def authenticate(self, credentials: AuthCredentials) -> AuthResult: ...
