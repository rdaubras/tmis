from tmis.ai_governance.lineage.ports import LineageStorePort
from tmis.ai_governance.lineage.schemas import (
    LineageExplanation,
    LineageRecord,
    new_lineage_record_id,
)


class LineageEngine:
    """Extends `tmis.cabinet_knowledge.lineage.LineageEngine`'s
    pattern to AI productions: records where a production's inputs
    came from, and — when it revises an earlier production — the
    revision chain back to the original."""

    def __init__(self, store: LineageStorePort) -> None:
        self._store = store

    def record_origin(
        self,
        firm_id: str,
        production_id: str,
        source_refs: tuple[str, ...],
        actor: str,
        revised_from_id: str | None = None,
    ) -> LineageRecord:
        record = LineageRecord(
            id=new_lineage_record_id(),
            firm_id=firm_id,
            production_id=production_id,
            source_refs=source_refs,
            actor=actor,
            revised_from_id=revised_from_id,
        )
        self._store.add(record)
        return record

    def explain(self, firm_id: str, production_id: str) -> LineageExplanation:
        records = self._store.list_for_production(firm_id, production_id)

        chain: list[str] = []
        visited: set[str] = set()
        current_id: str | None = production_id
        while current_id is not None and current_id not in visited:
            visited.add(current_id)
            chain.append(current_id)
            latest = self._store.get_latest(firm_id, current_id)
            current_id = latest.revised_from_id if latest is not None else None
        chain.reverse()

        return LineageExplanation(
            production_id=production_id,
            origin_records=tuple(records),
            revision_chain=tuple(chain),
        )
