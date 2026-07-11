from collections.abc import Awaitable, Callable

from tmis.ai_fabric.batch.schemas import BatchRequest, BatchResult
from tmis.ai_fabric.latency_optimizer.engine import LatencyOptimizer


class BatchProcessor:
    """The sprint's "BATCH" module: runs several requests concurrently
    (bounded, via `tmis.ai_fabric.latency_optimizer`) and isolates each
    request's failure so one bad prompt cannot fail an entire batch."""

    def __init__(self, latency_optimizer: LatencyOptimizer | None = None) -> None:
        self._latency_optimizer = latency_optimizer or LatencyOptimizer()

    async def run_batch(
        self,
        requests: list[BatchRequest],
        executor: Callable[[BatchRequest], Awaitable[str]],
    ) -> list[BatchResult]:
        async def _run_one(request: BatchRequest) -> BatchResult:
            try:
                text = await executor(request)
                return BatchResult(request_id=request.request_id, text=text)
            except Exception as exc:
                return BatchResult(request_id=request.request_id, text="", error=str(exc))

        return await self._latency_optimizer.run_parallel([_run_one(r) for r in requests])
