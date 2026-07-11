from tmis.cabinet_knowledge.governance.schemas import GovernanceEvent


class InMemoryGovernanceStore:
    def __init__(self) -> None:
        self._events: list[GovernanceEvent] = []

    def append(self, event: GovernanceEvent) -> None:
        self._events.append(event)

    def history(self, firm_id: str, knowledge_object_id: str) -> list[GovernanceEvent]:
        return [
            e
            for e in self._events
            if e.firm_id == firm_id and e.knowledge_object_id == knowledge_object_id
        ]
