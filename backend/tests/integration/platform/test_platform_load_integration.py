import asyncio
import time

from tmis.platform.performance.concurrency import bounded_gather
from tmis.platform.rate_limiting.brute_force import BruteForceProtector
from tmis.platform.rate_limiting.limiter import InMemoryRateLimiter
from tmis.platform.rate_limiting.schemas import LockoutPolicy, RateLimitPolicy


async def test_rate_limiter_holds_up_under_concurrent_bursts_from_many_identities() -> None:
    """Load smoke test (see docs/47-guide-securite-entreprise.md — Tests
    de charge): simulates 50 identities each firing 20 concurrent
    requests through the rate limiter and asserts every identity is
    capped at its configured limit, with no cross-identity leakage,
    under real concurrency (not just sequential calls)."""
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_window=10, window_seconds=60))

    async def _hit(identity: str) -> bool:
        await asyncio.sleep(0)
        return limiter.check(identity).allowed

    results_by_identity: dict[str, list[bool]] = {}
    for identity in [f"user-{i}" for i in range(50)]:
        coroutines = [_hit(identity) for _ in range(20)]
        results_by_identity[identity] = await bounded_gather(coroutines, max_concurrency=20)

    for identity, results in results_by_identity.items():
        allowed_count = sum(1 for r in results if r)
        assert allowed_count == 10, f"{identity} should allow exactly 10 of 20 requests"


async def test_brute_force_protector_locks_out_under_concurrent_failed_attempts() -> None:
    protector = BruteForceProtector(LockoutPolicy(max_failed_attempts=5, window_seconds=300))

    async def _fail(identity: str) -> None:
        await asyncio.sleep(0)
        protector.record_failure(identity)

    await bounded_gather([_fail("ip:10.0.0.1") for _ in range(5)], max_concurrency=5)

    status = protector.status("ip:10.0.0.1")
    assert status.locked is True


def test_rate_limiter_check_stays_fast_under_a_realistic_request_volume() -> None:
    """Basic scale smoke test: 10,000 checks across 100 identities must
    complete quickly — a regression here would signal an accidental
    O(n) scan creeping into what should be an O(1) dict lookup."""
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_window=1000, window_seconds=60))

    start = time.perf_counter()
    for i in range(10_000):
        limiter.check(f"user-{i % 100}")
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
