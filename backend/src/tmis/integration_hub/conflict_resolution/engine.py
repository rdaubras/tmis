from tmis.integration_hub.conflict_resolution.ports import ConflictStrategyPort
from tmis.integration_hub.conflict_resolution.schemas import (
    ConflictContext,
    ConflictResolution,
    ConflictStrategy,
)
from tmis.integration_hub.conflict_resolution.strategies import default_strategies


class UnknownConflictStrategyError(KeyError):
    pass


class ConflictResolutionEngine:
    def __init__(
        self, strategies: dict[ConflictStrategy, ConflictStrategyPort] | None = None
    ) -> None:
        self._strategies: dict[ConflictStrategy, ConflictStrategyPort] = strategies or {
            s.strategy: s for s in default_strategies()
        }

    def register(self, strategy: ConflictStrategyPort) -> None:
        self._strategies[strategy.strategy] = strategy

    def resolve(self, context: ConflictContext, strategy: ConflictStrategy) -> ConflictResolution:
        impl = self._strategies.get(strategy)
        if impl is None:
            raise UnknownConflictStrategyError(strategy)
        return impl.resolve(context)
