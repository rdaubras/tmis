from tmis.cabinet_os.time_tracking.schemas import TimeEntry


class InMemoryTimeEntryStore:
    """Implements `TimeEntryStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._entries: dict[str, TimeEntry] = {}

    def get(self, entry_id: str) -> TimeEntry | None:
        return self._entries.get(entry_id)

    def save(self, entry: TimeEntry) -> None:
        self._entries[entry.id] = entry

    def list_for_case(self, case_id: str) -> list[TimeEntry]:
        return [e for e in self._entries.values() if e.case_id == case_id]

    def list_for_collaborator(self, collaborator_id: str) -> list[TimeEntry]:
        return [e for e in self._entries.values() if e.collaborator_id == collaborator_id]

    def list_for_firm(self, firm_id: str) -> list[TimeEntry]:
        return [e for e in self._entries.values() if e.firm_id == firm_id]
