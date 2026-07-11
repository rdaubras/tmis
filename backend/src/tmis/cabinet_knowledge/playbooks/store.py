from tmis.cabinet_knowledge.playbooks.schemas import PlaybookInstance


class InMemoryPlaybookInstanceStore:
    def __init__(self) -> None:
        self._instances: dict[str, PlaybookInstance] = {}

    def save(self, instance: PlaybookInstance) -> None:
        self._instances[instance.id] = instance

    def get(self, instance_id: str) -> PlaybookInstance | None:
        return self._instances.get(instance_id)

    def list_for_firm(self, firm_id: str) -> list[PlaybookInstance]:
        return [i for i in self._instances.values() if i.firm_id == firm_id]
