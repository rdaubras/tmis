from tmis.integration_hub.authentication.schemas import AuthCredentials, AuthMethod, AuthResult


def _require(credentials: AuthCredentials, *fields: str) -> AuthResult:
    missing = [f for f in fields if not credentials.values.get(f)]
    if missing:
        return AuthResult(authenticated=False, detail=f"Champs manquants : {', '.join(missing)}")
    return AuthResult(authenticated=True, detail="Authentification réussie")


class OAuth2Strategy:
    method = AuthMethod.OAUTH2

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        return _require(credentials, "client_id", "client_secret", "access_token")


class OIDCStrategy:
    method = AuthMethod.OIDC

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        return _require(credentials, "issuer", "id_token")


class ApiKeyStrategy:
    method = AuthMethod.API_KEY

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        return _require(credentials, "api_key")


class JWTStrategy:
    method = AuthMethod.JWT

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        return _require(credentials, "token")


class CertificateStrategy:
    method = AuthMethod.CERTIFICATE

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        return _require(credentials, "certificate_fingerprint")


DEFAULT_STRATEGIES = (
    OAuth2Strategy(),
    OIDCStrategy(),
    ApiKeyStrategy(),
    JWTStrategy(),
    CertificateStrategy(),
)
