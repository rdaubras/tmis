from tmis.identity_platform.authentication.ports import AuthStrategyPort
from tmis.identity_platform.authentication.schemas import AuthCredentials, AuthMethod, AuthResult


class UnknownAuthMethodError(KeyError):
    pass


class AuthenticationEngine:
    """Dispatches to the registered strategy for a credential's
    method — the sprint's "moteur complet d'authentification"."""

    def __init__(self, strategies: dict[AuthMethod, AuthStrategyPort] | None = None) -> None:
        self._strategies: dict[AuthMethod, AuthStrategyPort] = (
            dict(strategies) if strategies is not None else {}
        )

    def register(self, strategy: AuthStrategyPort) -> None:
        self._strategies[strategy.method] = strategy

    async def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        strategy = self._strategies.get(credentials.method)
        if strategy is None:
            raise UnknownAuthMethodError(credentials.method)
        return await strategy.authenticate(credentials)
