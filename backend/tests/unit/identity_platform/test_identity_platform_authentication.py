import pytest

from tmis.identity_platform.authentication.engine import (
    AuthenticationEngine,
    UnknownAuthMethodError,
)
from tmis.identity_platform.authentication.schemas import AuthCredentials, AuthMethod, AuthResult
from tmis.identity_platform.oauth2.engine import OAuth2Engine
from tmis.identity_platform.oauth2.schemas import OAuth2Error
from tmis.identity_platform.oauth2.store import (
    InMemoryAuthorizationCodeStore,
    InMemoryOAuth2ClientStore,
)
from tmis.identity_platform.openid_connect.engine import OpenIdConnectEngine


def _oauth2_engine() -> OAuth2Engine:
    return OAuth2Engine(InMemoryOAuth2ClientStore(), InMemoryAuthorizationCodeStore())


def test_oauth2_authorization_code_grant_full_cycle() -> None:
    engine = _oauth2_engine()
    client, secret = engine.register_client("firm-1", ("https://app.example.com/callback",))

    code = engine.issue_authorization_code(
        client.client_id, "user-1", "firm-1", "https://app.example.com/callback"
    )
    tokens = engine.exchange_code(
        client.client_id, secret, code, "https://app.example.com/callback"
    )

    assert tokens.user_id == "user-1"
    assert tokens.firm_id == "firm-1"
    assert tokens.access_token


def test_oauth2_rejects_wrong_client_secret() -> None:
    engine = _oauth2_engine()
    client, _secret = engine.register_client("firm-1", ("https://app.example.com/callback",))
    code = engine.issue_authorization_code(
        client.client_id, "user-1", "firm-1", "https://app.example.com/callback"
    )

    with pytest.raises(OAuth2Error):
        engine.exchange_code(
            client.client_id, "wrong-secret", code, "https://app.example.com/callback"
        )


def test_oauth2_authorization_code_is_single_use() -> None:
    engine = _oauth2_engine()
    client, secret = engine.register_client("firm-1", ("https://app.example.com/callback",))
    code = engine.issue_authorization_code(
        client.client_id, "user-1", "firm-1", "https://app.example.com/callback"
    )
    engine.exchange_code(client.client_id, secret, code, "https://app.example.com/callback")

    with pytest.raises(OAuth2Error):
        engine.exchange_code(client.client_id, secret, code, "https://app.example.com/callback")


def test_openid_connect_exchange_adds_id_token_on_top_of_oauth2() -> None:
    oauth2 = _oauth2_engine()
    oidc = OpenIdConnectEngine(oauth2)
    client, secret = oauth2.register_client("firm-1", ("https://app.example.com/callback",))
    code = oauth2.issue_authorization_code(
        client.client_id, "user-1", "firm-1", "https://app.example.com/callback"
    )

    response = oidc.exchange_code(
        client.client_id,
        secret,
        code,
        "https://app.example.com/callback",
        email="user1@example.com",
        display_name="User One",
    )

    assert response.access_token
    assert response.id_token
    assert response.id_token != response.access_token


def test_authentication_engine_dispatches_to_registered_strategy() -> None:
    class _AlwaysAllowStrategy:
        method = AuthMethod.PASSWORDLESS

        async def authenticate(self, credentials: AuthCredentials) -> AuthResult:
            return AuthResult(authenticated=True, user_id="user-1")

    engine = AuthenticationEngine()
    engine.register(_AlwaysAllowStrategy())

    import asyncio

    result = asyncio.run(
        engine.authenticate(AuthCredentials(method=AuthMethod.PASSWORDLESS, firm_id="firm-1"))
    )

    assert result.authenticated is True


def test_authentication_engine_raises_for_unregistered_method() -> None:
    engine = AuthenticationEngine()

    import asyncio

    with pytest.raises(UnknownAuthMethodError):
        asyncio.run(
            engine.authenticate(AuthCredentials(method=AuthMethod.MAGIC_LINK, firm_id="firm-1"))
        )
