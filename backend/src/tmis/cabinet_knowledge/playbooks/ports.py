from typing import Protocol

from tmis.cabinet_knowledge.playbooks.schemas import PlaybookInstance


class PlaybookInstanceStorePort(Protocol):
    def save(self, instance: PlaybookInstance) -> None: ...

    def get(self, instance_id: str) -> PlaybookInstance | None: ...

    def list_for_firm(self, firm_id: str) -> list[PlaybookInstance]: ...
