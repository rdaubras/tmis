import uuid

from tmis.ai.memory.ports import MemoryStorePort


class CaseMemory:
    """Long-term memory scoped to a `case` (facts and summaries learned
    across multiple analyses of the same dossier)."""

    def __init__(self, store: MemoryStorePort) -> None:
        self._store = store

    def _key(self, case_id: uuid.UUID) -> str:
        return f"case:{case_id}"

    async def add_note(self, case_id: uuid.UUID, note: str) -> None:
        await self._store.append(self._key(case_id), note)

    async def get_notes(self, case_id: uuid.UUID) -> list[str]:
        return await self._store.get(self._key(case_id))

    async def clear(self, case_id: uuid.UUID) -> None:
        await self._store.clear(self._key(case_id))
