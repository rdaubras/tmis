from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """A fixed-window rate limit policy (see
    docs/47-guide-securite-entreprise.md — Rate Limiting)."""

    requests_per_window: int = 60
    window_seconds: int = 60
    burst: int = 0


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: float = 0.0
    limit: int = 0


@dataclass(frozen=True, slots=True)
class LockoutPolicy:
    """Brute-force protection policy: after `max_failed_attempts`
    failures within `window_seconds`, the identity is locked out for
    `lockout_seconds`."""

    max_failed_attempts: int = 5
    window_seconds: int = 300
    lockout_seconds: int = 900


@dataclass(frozen=True, slots=True)
class LockoutStatus:
    locked: bool
    remaining_attempts: int
    retry_after_seconds: float = 0.0
