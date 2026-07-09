from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisMemoryStore:
    """Implements `MemoryStorePort` on top of a Redis list per key.

    Production backend: survives process restarts and is shared across
    API workers, unlike `InMemoryStore`.
    """

    def __init__(self, client: "Redis", *, key_prefix: str = "tmis:memory:") -> None:
        self._client = client
        self._key_prefix = key_prefix

    def _full_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> list[str]:
        values = await self._client.lrange(self._full_key(key), 0, -1)  # type: ignore[misc]
        return [v.decode() if isinstance(v, bytes) else v for v in values]

    async def append(self, key: str, value: str) -> None:
        await self._client.rpush(self._full_key(key), value)  # type: ignore[misc]

    async def clear(self, key: str) -> None:
        await self._client.delete(self._full_key(key))
