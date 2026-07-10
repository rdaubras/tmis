from datetime import UTC, datetime, timedelta

from tmis.platform.rate_limiting.schemas import RateLimitPolicy, RateLimitResult


class InMemoryRateLimiter:
    """Implements `RateLimiterPort`: a fixed-window counter per
    identity, with a configurable window size (see
    docs/47-guide-securite-entreprise.md — Rate Limiting). Mirrors
    `tmis.cabinet_os.public_api.rate_limiter.InMemoryRateLimiter`
    (Sprint 9), generalized to a configurable window rather than a
    fixed one minute, and promoted to the platform layer so any new
    endpoint can reuse it without depending on `cabinet_os`."""

    def __init__(self, policy: RateLimitPolicy | None = None) -> None:
        self._policy = policy or RateLimitPolicy()
        self._windows: dict[str, tuple[datetime, int]] = {}

    def check(self, identity: str) -> RateLimitResult:
        now = datetime.now(UTC)
        window = timedelta(seconds=self._policy.window_seconds)
        window_start, count = self._windows.get(identity, (now, 0))
        if now - window_start >= window:
            window_start, count = now, 0
        count += 1
        self._windows[identity] = (window_start, count)

        limit = self._policy.requests_per_window + self._policy.burst
        if count > limit:
            retry_after = (window_start + window - now).total_seconds()
            return RateLimitResult(
                allowed=False, remaining=0, retry_after_seconds=max(0.0, retry_after), limit=limit
            )
        return RateLimitResult(allowed=True, remaining=limit - count, limit=limit)
