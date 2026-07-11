from typing import Protocol

from tmis.cabinet_knowledge.governance.schemas import GovernanceEvent


class GovernanceStorePort(Protocol):
    def append(self, event: GovernanceEvent) -> None: ...

    def history(self, firm_id: str, knowledge_object_id: str) -> list[GovernanceEvent]: ...
