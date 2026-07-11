from tmis.workflow_automation.action_engine.schemas import ActionLogEntry


class InMemoryActionLogStore:
    def __init__(self) -> None:
        self._entries: list[ActionLogEntry] = []

    def add(self, entry: ActionLogEntry) -> None:
        self._entries.append(entry)

    def list_for_execution(self, firm_id: str, execution_id: str) -> list[ActionLogEntry]:
        return [
            e
            for e in self._entries
            if e.firm_id == firm_id and e.execution_id == execution_id
        ]
