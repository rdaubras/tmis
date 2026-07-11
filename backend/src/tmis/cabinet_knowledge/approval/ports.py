from typing import Protocol

from tmis.cabinet_knowledge.approval.schemas import ApprovalRecord


class ApprovalStorePort(Protocol):
    def save(self, record: ApprovalRecord) -> None: ...

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[ApprovalRecord]: ...
