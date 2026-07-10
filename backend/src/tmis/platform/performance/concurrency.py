import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def bounded_gather(coroutines: Iterable[Awaitable[T]], max_concurrency: int) -> list[T]:
    """Runs every coroutine in `coroutines` concurrently, but never
    more than `max_concurrency` at once (see
    docs/50-guide-performance.md — Parallélisation des workflows IA).
    Useful wherever TMIS fans out several `TMISKernel.complete()` calls
    at once (e.g. drafting several independent sections) — bounded so
    it cannot overwhelm a rate-limited model provider."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_run(c) for c in coroutines))
