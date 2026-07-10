from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tmis.platform.rate_limiting.schemas import LockoutPolicy, LockoutStatus


@dataclass(slots=True)
class _AttemptWindow:
    window_start: datetime
    failures: int
    locked_until: datetime | None = None


class BruteForceProtector:
    """Implements `BruteForceProtectorPort` (see
    docs/47-guide-securite-entreprise.md — Protection brute force):
    counts failed attempts per identity (typically `ip:username`)
    within a rolling window and locks the identity out once the
    threshold is reached. A successful attempt clears the count —
    only *failures* accumulate towards a lockout."""

    def __init__(self, policy: LockoutPolicy | None = None) -> None:
        self._policy = policy or LockoutPolicy()
        self._state: dict[str, _AttemptWindow] = {}

    def record_failure(self, identity: str) -> LockoutStatus:
        now = datetime.now(UTC)
        entry = self._state.get(identity)
        if entry is not None and entry.locked_until is not None and now < entry.locked_until:
            return LockoutStatus(
                locked=True,
                remaining_attempts=0,
                retry_after_seconds=(entry.locked_until - now).total_seconds(),
            )

        window = timedelta(seconds=self._policy.window_seconds)
        if entry is None or now - entry.window_start >= window:
            entry = _AttemptWindow(window_start=now, failures=0)

        entry.failures += 1
        if entry.failures >= self._policy.max_failed_attempts:
            entry.locked_until = now + timedelta(seconds=self._policy.lockout_seconds)
            self._state[identity] = entry
            return LockoutStatus(
                locked=True, remaining_attempts=0, retry_after_seconds=self._policy.lockout_seconds
            )

        self._state[identity] = entry
        return LockoutStatus(
            locked=False, remaining_attempts=self._policy.max_failed_attempts - entry.failures
        )

    def record_success(self, identity: str) -> None:
        self._state.pop(identity, None)

    def status(self, identity: str) -> LockoutStatus:
        entry = self._state.get(identity)
        if entry is None:
            return LockoutStatus(locked=False, remaining_attempts=self._policy.max_failed_attempts)
        now = datetime.now(UTC)
        if entry.locked_until is not None and now < entry.locked_until:
            return LockoutStatus(
                locked=True,
                remaining_attempts=0,
                retry_after_seconds=(entry.locked_until - now).total_seconds(),
            )
        return LockoutStatus(
            locked=False,
            remaining_attempts=max(0, self._policy.max_failed_attempts - entry.failures),
        )
