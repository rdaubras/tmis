from tmis.core.security import create_access_token
from tmis.identity_platform.oauth2.engine import OAuth2Engine
from tmis.identity_platform.openid_connect.schemas import OidcTokenResponse


class OpenIdConnectEngine:
    """The real OIDC ID-token issuance
    `platform.security.sso.OidcProviderPort` was declared an
    "architecture-only extension point... no implementation ships this
    sprint" for (Sprint 10). Composes `oauth2.OAuth2Engine` for the
    authorization-code + access/refresh token mechanics and only adds
    the OIDC-specific ID token — never reimplements token issuance."""

    def __init__(self, oauth2_engine: OAuth2Engine) -> None:
        self._oauth2 = oauth2_engine

    def exchange_code(
        self,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        *,
        email: str,
        display_name: str,
    ) -> OidcTokenResponse:
        tokens = self._oauth2.exchange_code(client_id, client_secret, code, redirect_uri)
        id_token = create_access_token(
            tokens.user_id,
            {"firm_id": tokens.firm_id, "email": email, "name": display_name},
        )
        return OidcTokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            id_token=id_token,
        )
