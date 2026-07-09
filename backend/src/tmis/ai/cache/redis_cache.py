from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisCache:
    """Implements `CachePort` on top of Redis (production backend).

    A thin wrapper: all cache semantics (TTL, key format) live here so
    callers stay backend-agnostic, per `tmis.ai.cache.ports.CachePort`.
    """

    def __init__(self, client: "Redis", *, key_prefix: str = "tmis:cache:") -> None:
        self._client = client
        self._key_prefix = key_prefix

    def _full_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> str | None:
        value = await self._client.get(self._full_key(key))
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        await self._client.set(self._full_key(key), value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(self._full_key(key))

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(self._full_key(key)))
