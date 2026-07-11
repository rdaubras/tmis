from tmis.cabinet_knowledge.approval.schemas import ApprovalRecord


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._records: list[ApprovalRecord] = []

    def save(self, record: ApprovalRecord) -> None:
        self._records.append(record)

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[ApprovalRecord]:
        return [
            r
            for r in self._records
            if r.firm_id == firm_id and r.knowledge_object_id == knowledge_object_id
        ]
