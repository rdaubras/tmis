from typing import Protocol

from tmis.platform.rate_limiting.schemas import LockoutStatus, RateLimitResult


class RateLimiterPort(Protocol):
    """Port implemented by every interchangeable rate limiter — a real
    deployment would swap the in-memory reference implementation for a
    distributed one (e.g. Redis token bucket) behind this same port
    (see docs/47-guide-securite-entreprise.md)."""

    def check(self, identity: str) -> RateLimitResult: ...


class BruteForceProtectorPort(Protocol):
    """Port implemented by every interchangeable brute-force
    protector — tracks failed authentication attempts per identity
    (typically `f"{ip}:{username}"`) and locks it out after too many
    failures."""

    def record_failure(self, identity: str) -> LockoutStatus: ...

    def record_success(self, identity: str) -> None: ...

    def status(self, identity: str) -> LockoutStatus: ...
