from tmis.platform.rate_limiting.brute_force import BruteForceProtector
from tmis.platform.rate_limiting.limiter import InMemoryRateLimiter
from tmis.platform.rate_limiting.schemas import LockoutPolicy, RateLimitPolicy


def test_rate_limiter_allows_requests_within_the_window() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_window=3, window_seconds=60))

    results = [limiter.check("user-1") for _ in range(3)]

    assert all(r.allowed for r in results)
    assert results[-1].remaining == 0


def test_rate_limiter_blocks_once_the_limit_is_exceeded() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_window=2, window_seconds=60))

    limiter.check("user-1")
    limiter.check("user-1")
    blocked = limiter.check("user-1")

    assert blocked.allowed is False
    assert blocked.retry_after_seconds > 0


def test_rate_limiter_tracks_identities_independently() -> None:
    limiter = InMemoryRateLimiter(RateLimitPolicy(requests_per_window=1, window_seconds=60))

    limiter.check("user-1")
    other = limiter.check("user-2")

    assert other.allowed is True


def test_brute_force_protector_locks_out_after_threshold() -> None:
    protector = BruteForceProtector(LockoutPolicy(max_failed_attempts=3, window_seconds=300))

    protector.record_failure("ip:1.2.3.4")
    protector.record_failure("ip:1.2.3.4")
    third = protector.record_failure("ip:1.2.3.4")

    assert third.locked is True
    assert third.remaining_attempts == 0


def test_brute_force_protector_success_clears_failure_count() -> None:
    protector = BruteForceProtector(LockoutPolicy(max_failed_attempts=3, window_seconds=300))

    protector.record_failure("ip:1.2.3.4")
    protector.record_success("ip:1.2.3.4")
    status = protector.status("ip:1.2.3.4")

    assert status.locked is False
    assert status.remaining_attempts == 3


def test_brute_force_protector_status_reflects_lockout() -> None:
    protector = BruteForceProtector(LockoutPolicy(max_failed_attempts=1, window_seconds=300))

    protector.record_failure("ip:1.2.3.4")
    status = protector.status("ip:1.2.3.4")

    assert status.locked is True
    assert status.retry_after_seconds > 0
