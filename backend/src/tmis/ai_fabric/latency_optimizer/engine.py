import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.platform.performance.concurrency import bounded_gather

T = TypeVar("T")

_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_CONCURRENCY = 4


class LatencyOptimizer:
    """The sprint's "LATENCY OPTIMIZER": parallel execution, timeout,
    fallback, cancellation. Reuses
    `tmis.platform.performance.concurrency.bounded_gather` (Sprint 10)
    for bounded parallelism rather than reimplementing a semaphore
    pool."""

    def __init__(
        self,
        *,
        max_concurrency: int = _DEFAULT_MAX_CONCURRENCY,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._max_concurrency = max_concurrency
        self._timeout_seconds = timeout_seconds

    async def run_with_timeout(self, coro: Awaitable[T]) -> T:
        return await asyncio.wait_for(coro, timeout=self._timeout_seconds)

    async def run_parallel(self, coroutines: Iterable[Awaitable[T]]) -> list[T]:
        return await bounded_gather(coroutines, self._max_concurrency)

    def fastest_available(self, candidates: list[ModelDescriptor]) -> ModelDescriptor | None:
        available = [model for model in candidates if model.availability]
        if not available:
            return None
        return min(available, key=lambda model: model.avg_latency_ms)
