from tmis.cabinet_knowledge.governance.ports import GovernanceStorePort
from tmis.cabinet_knowledge.governance.schemas import (
    ALLOWED_TRANSITIONS,
    GovernanceEvent,
    InvalidTransitionError,
    new_governance_event_id,
)
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeStatus


class GovernanceEngine:
    """The knowledge lifecycle state machine (see the sprint's
    "KNOWLEDGE GOVERNANCE" spec: brouillon / en révision / validé /
    obsolète / archivé) — the only place allowed to mutate a
    `KnowledgeObject.status`, and every mutation is recorded as a
    `GovernanceEvent`, satisfying "toutes les modifications sont
    historisées"."""

    def __init__(self, store: GovernanceStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def transition(
        self,
        firm_id: str,
        knowledge_object_id: str,
        to_status: KnowledgeStatus,
        actor: str,
        reason: str | None = None,
    ) -> KnowledgeObject:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        if obj is None:
            raise KeyError(knowledge_object_id)
        if to_status not in ALLOWED_TRANSITIONS[obj.status]:
            raise InvalidTransitionError(obj.status, to_status)
        from_status = obj.status
        updated = self._knowledge_space.set_status(firm_id, knowledge_object_id, to_status)
        self._store.append(
            GovernanceEvent(
                id=new_governance_event_id(),
                firm_id=firm_id,
                knowledge_object_id=knowledge_object_id,
                from_status=from_status,
                to_status=to_status,
                actor=actor,
                reason=reason,
            )
        )
        return updated

    def history(self, firm_id: str, knowledge_object_id: str) -> list[GovernanceEvent]:
        return self._store.history(firm_id, knowledge_object_id)
