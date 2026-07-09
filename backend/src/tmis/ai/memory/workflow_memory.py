import uuid

from tmis.ai.memory.ports import MemoryStorePort


class WorkflowMemory:
    """Memory of a single workflow run: the trace of steps executed, used
    for debugging and for the Evaluation module."""

    def __init__(self, store: MemoryStorePort) -> None:
        self._store = store

    def _key(self, workflow_id: uuid.UUID) -> str:
        return f"workflow:{workflow_id}"

    async def record_step(self, workflow_id: uuid.UUID, step: str) -> None:
        await self._store.append(self._key(workflow_id), step)

    async def get_trace(self, workflow_id: uuid.UUID) -> list[str]:
        return await self._store.get(self._key(workflow_id))
