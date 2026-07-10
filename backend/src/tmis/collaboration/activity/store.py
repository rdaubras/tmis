from tmis.collaboration.activity.schemas import ActivityEntry


class InMemoryActivityStore:
    """Implements `ActivityStorePort` — append-only: entries are never
    updated or removed once recorded."""

    def __init__(self) -> None:
        self._entries: list[ActivityEntry] = []

    def save(self, entry: ActivityEntry) -> None:
        self._entries.append(entry)

    def list_for_workspace(self, workspace_id: str) -> list[ActivityEntry]:
        return [e for e in self._entries if e.workspace_id == workspace_id]

    def list_all(self) -> list[ActivityEntry]:
        return list(self._entries)
