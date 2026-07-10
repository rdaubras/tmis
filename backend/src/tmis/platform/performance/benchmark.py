import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    name: str
    iterations: int
    total_seconds: float
    mean_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float


def benchmark(name: str, fn: Callable[[], object], iterations: int = 100) -> BenchmarkResult:
    """Times `fn` over `iterations` calls and reports mean/p95/min/max
    latency (see docs/50-guide-performance.md — Benchmarks). Meant for
    micro-benchmarking a hot path (a query, a serialization step, a
    cache lookup) in a test or a one-off script — not a substitute for
    a real load-testing tool against a running deployment."""
    durations_ms: list[float] = []
    start_all = time.perf_counter()
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        durations_ms.append((time.perf_counter() - start) * 1000)
    total_seconds = time.perf_counter() - start_all

    sorted_durations = sorted(durations_ms)
    p95_index = min(len(sorted_durations) - 1, int(len(sorted_durations) * 0.95))
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_seconds=total_seconds,
        mean_ms=sum(durations_ms) / len(durations_ms),
        p95_ms=sorted_durations[p95_index],
        min_ms=sorted_durations[0],
        max_ms=sorted_durations[-1],
    )
