from tmis.cabinet_knowledge.approval.ports import ApprovalStorePort
from tmis.cabinet_knowledge.approval.schemas import ApprovalRecord, new_approval_record_id
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeStatus


class NotValidatedError(ValueError):
    pass


class ApprovalEngine:
    """The publication gate: a `VALIDATED` knowledge object is not yet
    visible to `search`/`recommendations` until an explicit human
    `publish()` call — content correctness (validation/) and
    publication (approval/) are deliberately two separate human
    decisions."""

    def __init__(self, store: ApprovalStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def is_publishable(self, firm_id: str, knowledge_object_id: str) -> bool:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        return obj is not None and obj.status is KnowledgeStatus.VALIDATED

    def publish(self, firm_id: str, knowledge_object_id: str, approver: str) -> KnowledgeObject:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        if obj is None:
            raise KeyError(knowledge_object_id)
        if obj.status is not KnowledgeStatus.VALIDATED:
            raise NotValidatedError(
                f"{knowledge_object_id} is {obj.status.value}, expected validated"
            )
        obj.is_published = True
        self._store.save(
            ApprovalRecord(
                id=new_approval_record_id(),
                firm_id=firm_id,
                knowledge_object_id=knowledge_object_id,
                approver=approver,
            )
        )
        return obj

    def unpublish(self, firm_id: str, knowledge_object_id: str) -> KnowledgeObject:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        if obj is None:
            raise KeyError(knowledge_object_id)
        obj.is_published = False
        return obj

    def history(self, firm_id: str, knowledge_object_id: str) -> list[ApprovalRecord]:
        return self._store.list_for_object(firm_id, knowledge_object_id)
