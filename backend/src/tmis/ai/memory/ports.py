from typing import Protocol


class MemoryStorePort(Protocol):
    """Low-level key/value port shared by every memory type.

    Higher-level memory classes (`ConversationMemory`, `CaseMemory`, ...)
    build namespaced keys on top of this port; they never assume a
    particular storage technology.
    """

    async def get(self, key: str) -> list[str]: ...

    async def append(self, key: str, value: str) -> None: ...

    async def clear(self, key: str) -> None: ...
