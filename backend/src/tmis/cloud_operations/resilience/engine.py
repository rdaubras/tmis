from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TypeVar

from tmis.cloud_operations.resilience.schemas import (
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitState,
)

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    """Per-named-dependency circuit breaker — confirmed genuinely new
    (no circuit breaker exists anywhere in TMIS). Complements rather
    than replaces `ai_fabric.retry.RetryPolicy` (retries the same
    call) and `ai_fabric.fallback.FallbackEngine` (switches to a
    different model): once a dependency is clearly failing, this
    engine stops calling it for a cooldown period instead of letting
    retries keep hammering it."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._circuits: dict[str, CircuitBreakerState] = {}

    def _state_for(self, name: str) -> CircuitBreakerState:
        return self._circuits.setdefault(name, CircuitBreakerState(name=name))

    def allow_request(self, name: str) -> bool:
        circuit = self._state_for(name)
        if circuit.state is CircuitState.OPEN:
            assert circuit.opened_at is not None
            elapsed = (datetime.now(UTC) - circuit.opened_at).total_seconds()
            if elapsed >= self._config.recovery_timeout_seconds:
                circuit.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def force_open(self, name: str) -> CircuitBreakerState:
        """Directly trips a circuit open, bypassing the failure
        threshold — used by `chaos_testing` to simulate a dependency
        outage without needing to know that circuit's configured
        threshold."""
        circuit = self._state_for(name)
        circuit.state = CircuitState.OPEN
        circuit.failure_count = self._config.failure_threshold
        circuit.opened_at = datetime.now(UTC)
        return circuit

    def record_success(self, name: str) -> None:
        circuit = self._state_for(name)
        circuit.state = CircuitState.CLOSED
        circuit.failure_count = 0
        circuit.opened_at = None

    def record_failure(self, name: str) -> None:
        circuit = self._state_for(name)
        circuit.failure_count += 1
        should_open = (
            circuit.state is CircuitState.HALF_OPEN
            or circuit.failure_count >= self._config.failure_threshold
        )
        if should_open:
            circuit.state = CircuitState.OPEN
            circuit.opened_at = datetime.now(UTC)

    async def call(self, name: str, operation: Callable[[], Awaitable[T]]) -> T:
        if not self.allow_request(name):
            raise CircuitOpenError(name)
        try:
            result = await operation()
        except Exception:
            self.record_failure(name)
            raise
        else:
            self.record_success(name)
            return result

    def state(self, name: str) -> CircuitBreakerState:
        return self._state_for(name)
