import time


class InMemoryCache:
    """Implements `CachePort` with a process-local dict.

    Default cache backend for local development and tests; `RedisCache` is
    the shared, persistent implementation used in staging/production.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at < time.monotonic():
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
