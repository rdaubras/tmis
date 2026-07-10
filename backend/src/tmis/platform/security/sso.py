from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SsoIdentity:
    """The result of a successful SSO authentication — deliberately
    provider-agnostic (OIDC and SAML both map onto this shape)."""

    subject: str
    email: str
    display_name: str
    firm_id: str
    raw_claims: dict[str, str]


class OidcProviderPort(Protocol):
    """Architecture-only extension point for a future OpenID Connect
    integration (see docs/47-guide-securite-entreprise.md — SSO):
    no implementation ships this sprint, only the port a real OIDC
    client (Authlib, etc.) would implement — `authorization_url` for
    the redirect, `exchange_code` for the callback."""

    def authorization_url(self, redirect_uri: str, state: str) -> str: ...

    def exchange_code(self, code: str, redirect_uri: str) -> SsoIdentity: ...


class SamlProviderPort(Protocol):
    """Architecture-only extension point for a future SAML integration
    — mirrors `OidcProviderPort` so the rest of TMIS (login flow,
    session creation) does not need to know which protocol a given
    firm's identity provider uses."""

    def login_request_url(self, relay_state: str) -> str: ...

    def consume_assertion(self, saml_response: str) -> SsoIdentity: ...
