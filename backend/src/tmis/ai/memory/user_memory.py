import uuid

from tmis.ai.memory.ports import MemoryStorePort


class UserMemory:
    """Memory of a single user's preferences/recent activity across cases
    (e.g. preferred model provider, recent searches)."""

    def __init__(self, store: MemoryStorePort) -> None:
        self._store = store

    def _key(self, user_id: uuid.UUID) -> str:
        return f"user:{user_id}"

    async def record_activity(self, user_id: uuid.UUID, activity: str) -> None:
        await self._store.append(self._key(user_id), activity)

    async def get_recent_activity(self, user_id: uuid.UUID) -> list[str]:
        return await self._store.get(self._key(user_id))
