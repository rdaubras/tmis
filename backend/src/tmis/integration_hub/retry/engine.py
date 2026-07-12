import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BASE_DELAY_SECONDS = 0.1


class IntegrationRetryPolicy:
    """Retries a failing async connector call with exponential
    backoff — same shape as `workflow_automation.retry.WorkflowRetryPolicy`
    and `ai_fabric.retry.RetryPolicy`, reimplemented locally since the
    Legal Integration Hub is a distinct bounded context and does not
    import across `tmis.workflow_automation`/`tmis.ai_fabric`."""

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
