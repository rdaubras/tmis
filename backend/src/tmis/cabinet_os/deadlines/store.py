from tmis.cabinet_os.deadlines.schemas import Deadline


class InMemoryDeadlineStore:
    """Implements `DeadlineStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._deadlines: dict[str, Deadline] = {}

    def get(self, deadline_id: str) -> Deadline | None:
        return self._deadlines.get(deadline_id)

    def save(self, deadline: Deadline) -> None:
        self._deadlines[deadline.id] = deadline

    def list_for_firm(self, firm_id: str) -> list[Deadline]:
        return [d for d in self._deadlines.values() if d.firm_id == firm_id]

    def list_for_case(self, case_id: str) -> list[Deadline]:
        return [d for d in self._deadlines.values() if d.case_id == case_id]
