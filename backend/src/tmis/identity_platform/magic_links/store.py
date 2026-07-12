class InMemoryUsedMagicLinkStore:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def is_used(self, token: str) -> bool:
        return token in self._used

    def mark_used(self, token: str) -> None:
        self._used.add(token)
