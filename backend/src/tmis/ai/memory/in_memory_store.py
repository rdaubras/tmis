from collections import defaultdict


class InMemoryStore:
    """Implements `MemoryStorePort` with a process-local dict of lists.

    Default backend for local development and tests.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[str]] = defaultdict(list)

    async def get(self, key: str) -> list[str]:
        return list(self._store[key])

    async def append(self, key: str, value: str) -> None:
        self._store[key].append(value)

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)
