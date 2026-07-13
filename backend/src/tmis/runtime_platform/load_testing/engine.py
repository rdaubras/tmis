import asyncio
import time
from collections.abc import Awaitable, Callable

from tmis.runtime_platform.load_testing.schemas import LoadTestPreset, LoadTestReport


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * percentile))
    return ordered[index]


class LoadTestingEngine:
    """The Sprint 23 Phase 1 audit found no load-testing
    infrastructure anywhere in TMIS (no Locust/k6 config, no custom
    generator). Rather than shelling out to an external tool this
    codebase has no dependency on, this is an in-process virtual-user
    simulator: it runs `concurrent_users` `asyncio` tasks against a
    caller-supplied `target` coroutine and measures latency/
    throughput/error rate — a simulation, not real network load,
    exactly the same honesty trade-off `cloud_operations.
    chaos_testing.ChaosTestingEngine` already makes (simulating a
    dependency outage via circuit state rather than real
    infrastructure disruption)."""

    async def run(
        self,
        preset: LoadTestPreset | int,
        target: Callable[[], Awaitable[None]],
        *,
        requests_per_user: int = 1,
    ) -> LoadTestReport:
        concurrent_users = int(preset)
        latencies: list[float] = []
        errors = 0
        start = time.perf_counter()

        async def _run_user() -> None:
            nonlocal errors
            for _ in range(requests_per_user):
                request_start = time.perf_counter()
                try:
                    await target()
                except Exception:  # noqa: BLE001 - a failed request is a measured outcome
                    errors += 1
                latencies.append((time.perf_counter() - request_start) * 1000)

        await asyncio.gather(*(_run_user() for _ in range(concurrent_users)))
        duration_seconds = time.perf_counter() - start
        total_requests = len(latencies)
        return LoadTestReport(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            success_count=total_requests - errors,
            error_count=errors,
            avg_latency_ms=sum(latencies) / total_requests if total_requests else 0.0,
            p95_latency_ms=_percentile(latencies, 0.95),
            throughput_rps=total_requests / duration_seconds if duration_seconds > 0 else 0.0,
            duration_seconds=duration_seconds,
        )
