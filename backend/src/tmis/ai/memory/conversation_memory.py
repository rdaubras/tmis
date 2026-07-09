import uuid

from tmis.ai.memory.ports import MemoryStorePort


class ConversationMemory:
    """Short-term memory of a chat thread (see docs/06-strategie-rag.md)."""

    def __init__(self, store: MemoryStorePort) -> None:
        self._store = store

    def _key(self, conversation_id: uuid.UUID) -> str:
        return f"conversation:{conversation_id}"

    async def add_message(self, conversation_id: uuid.UUID, role: str, content: str) -> None:
        await self._store.append(self._key(conversation_id), f"{role}: {content}")

    async def get_history(self, conversation_id: uuid.UUID) -> list[str]:
        return await self._store.get(self._key(conversation_id))

    async def clear(self, conversation_id: uuid.UUID) -> None:
        await self._store.clear(self._key(conversation_id))
