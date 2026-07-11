import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_DELAY_SECONDS = 0.5


class RetryPolicy:
    """Retries a failing async operation with exponential backoff —
    the complement to `tmis.ai_fabric.fallback` (which switches
    *model*) for the case where the same model is worth retrying
    (e.g. a transient provider timeout)."""

    def __init__(
        self,
        *,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        base_delay_seconds: float = _DEFAULT_BASE_DELAY_SECONDS,
    ) -> None:
        self._max_attempts = max_attempts
        self._base_delay_seconds = base_delay_seconds

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            try:
                return await operation()
            except Exception as exc:
                last_error = exc
                if attempt < self._max_attempts - 1:
                    await asyncio.sleep(self._base_delay_seconds * (2**attempt))
        assert last_error is not None
        raise last_error
