from tmis.integration_hub.authentication.ports import AuthStrategyPort
from tmis.integration_hub.authentication.schemas import AuthCredentials, AuthMethod, AuthResult
from tmis.integration_hub.authentication.strategies import DEFAULT_STRATEGIES


class UnknownAuthMethodError(KeyError):
    pass


class AuthenticationEngine:
    """Dispatches to the registered strategy for a credential's
    method — "le choix du mécanisme dépend du système cible"."""

    def __init__(self, strategies: dict[AuthMethod, AuthStrategyPort] | None = None) -> None:
        self._strategies: dict[AuthMethod, AuthStrategyPort] = strategies or {
            s.method: s for s in DEFAULT_STRATEGIES
        }

    def register(self, strategy: AuthStrategyPort) -> None:
        self._strategies[strategy.method] = strategy

    def authenticate(self, credentials: AuthCredentials) -> AuthResult:
        strategy = self._strategies.get(credentials.method)
        if strategy is None:
            raise UnknownAuthMethodError(credentials.method)
        return strategy.authenticate(credentials)
