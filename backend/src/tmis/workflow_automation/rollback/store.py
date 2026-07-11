from tmis.workflow_automation.rollback.schemas import RollbackLogEntry


class InMemoryRollbackLogStore:
    def __init__(self) -> None:
        self._entries: list[RollbackLogEntry] = []

    def add(self, entry: RollbackLogEntry) -> None:
        self._entries.append(entry)

    def list_for_execution(self, firm_id: str, execution_id: str) -> list[RollbackLogEntry]:
        return [
            e
            for e in self._entries
            if e.firm_id == firm_id and e.execution_id == execution_id
        ]
