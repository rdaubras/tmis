import pytest

from tmis.integration_hub.authentication import (
    AuthCredentials,
    AuthenticationEngine,
    AuthMethod,
    AuthResult,
    OAuth2Strategy,
    UnknownAuthMethodError,
)
from tmis.integration_hub.security import IntegrationSecurityEngine, new_rotating_encryption
from tmis.platform.rate_limiting.limiter import InMemoryRateLimiter
from tmis.platform.security.secrets_rotation import InMemorySecretRotationStore
from tmis.platform.security.tenant_isolation import TenantAccessError, TenantContext


@pytest.mark.parametrize(
    ("method", "values"),
    [
        (AuthMethod.OAUTH2, {"client_id": "c", "client_secret": "s", "access_token": "t"}),
        (AuthMethod.OIDC, {"issuer": "i", "id_token": "t"}),
        (AuthMethod.API_KEY, {"api_key": "k"}),
        (AuthMethod.JWT, {"token": "t"}),
        (AuthMethod.CERTIFICATE, {"certificate_fingerprint": "f"}),
    ],
)
def test_authentication_engine_succeeds_with_required_fields(
    method: AuthMethod, values: dict[str, str]
) -> None:
    engine = AuthenticationEngine()
    result = engine.authenticate(AuthCredentials(method=method, values=values))
    assert result.authenticated is True


def test_authentication_engine_fails_with_missing_fields() -> None:
    engine = AuthenticationEngine()
    result = engine.authenticate(AuthCredentials(method=AuthMethod.API_KEY, values={}))
    assert result.authenticated is False
    assert "api_key" in result.detail


def test_authentication_engine_unknown_method_raises() -> None:
    engine = AuthenticationEngine(strategies={AuthMethod.OAUTH2: OAuth2Strategy()})
    with pytest.raises(UnknownAuthMethodError):
        engine.authenticate(AuthCredentials(method=AuthMethod.API_KEY, values={}))


def test_authentication_engine_register_overrides_strategy() -> None:
    engine = AuthenticationEngine()

    class AlwaysFail:
        method = AuthMethod.API_KEY

        def authenticate(self, credentials: AuthCredentials) -> AuthResult:
            return AuthResult(authenticated=False, detail="forcé")

    engine.register(AlwaysFail())
    result = engine.authenticate(
        AuthCredentials(method=AuthMethod.API_KEY, values={"api_key": "k"})
    )
    assert result.authenticated is False
    assert result.detail == "forcé"


def test_integration_security_engine_encrypt_decrypt_roundtrip() -> None:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    engine = IntegrationSecurityEngine(rotation, InMemoryRateLimiter())

    encrypted = engine.encrypt_config({"token": "secret-value"})
    assert encrypted["token"] != "secret-value"
    decrypted = engine.decrypt_config(encrypted)
    assert decrypted == {"token": "secret-value"}


def test_integration_security_engine_rate_limit() -> None:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    engine = IntegrationSecurityEngine(rotation, InMemoryRateLimiter())
    result = engine.check_rate_limit("connector-1")
    assert result.allowed is True


def test_integration_security_engine_tenant_isolation() -> None:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    engine = IntegrationSecurityEngine(rotation, InMemoryRateLimiter())
    context = TenantContext(firm_id="firm-1", actor_id="u1")

    engine.require_tenant(context, "firm-1")
    with pytest.raises(TenantAccessError):
        engine.require_tenant(context, "firm-2")
