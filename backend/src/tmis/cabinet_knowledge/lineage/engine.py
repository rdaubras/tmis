from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.lineage.ports import LineageStorePort
from tmis.cabinet_knowledge.lineage.schemas import (
    LineageExplanation,
    LineageRecord,
    new_lineage_record_id,
)


class LineageEngine:
    def __init__(
        self,
        store: LineageStorePort,
        knowledge_space: KnowledgeSpace,
        governance: GovernanceEngine,
    ) -> None:
        self._store = store
        self._knowledge_space = knowledge_space
        self._governance = governance

    def record_origin(
        self,
        firm_id: str,
        knowledge_object_id: str,
        source_refs: tuple[str, ...],
        actor: str,
        revised_from_id: str | None = None,
    ) -> LineageRecord:
        if self._knowledge_space.get(firm_id, knowledge_object_id) is None:
            raise KeyError(knowledge_object_id)
        record = LineageRecord(
            id=new_lineage_record_id(),
            firm_id=firm_id,
            knowledge_object_id=knowledge_object_id,
            source_refs=source_refs,
            actor=actor,
            revised_from_id=revised_from_id,
        )
        self._store.save(record)
        return record

    def explain(self, firm_id: str, knowledge_object_id: str) -> LineageExplanation:
        obj = self._knowledge_space.get(firm_id, knowledge_object_id)
        if obj is None:
            raise KeyError(knowledge_object_id)
        return LineageExplanation(
            knowledge_object_id=knowledge_object_id,
            current_version=obj.version,
            origin_records=tuple(self._store.list_for_object(firm_id, knowledge_object_id)),
            governance_events=tuple(self._governance.history(firm_id, knowledge_object_id)),
        )
