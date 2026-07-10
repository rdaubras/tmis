from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.public_api.schemas import RateLimitPolicy, RateLimitResult

_WINDOW = timedelta(minutes=1)


class InMemoryRateLimiter:
    """Implements `RateLimiterPort`: a fixed one-minute window counter
    per identity (see docs/44-guide-api-publique.md — Rate Limiting).
    A real deployment would swap this for a distributed limiter (e.g.
    Redis token bucket) behind the same port — nothing else changes.
    """

    def __init__(self, policy: RateLimitPolicy | None = None) -> None:
        self._policy = policy or RateLimitPolicy()
        self._windows: dict[str, tuple[datetime, int]] = {}

    def check(self, identity: str) -> RateLimitResult:
        now = datetime.now(UTC)
        window_start, count = self._windows.get(identity, (now, 0))
        if now - window_start >= _WINDOW:
            window_start, count = now, 0
        count += 1
        self._windows[identity] = (window_start, count)

        limit = self._policy.requests_per_minute + self._policy.burst
        if count > limit:
            retry_after = (window_start + _WINDOW - now).total_seconds()
            return RateLimitResult(
                allowed=False, remaining=0, retry_after_seconds=max(0.0, retry_after), limit=limit
            )
        return RateLimitResult(allowed=True, remaining=limit - count, limit=limit)
