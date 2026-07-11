from tmis.ai_governance.traceability.schemas import TraceEntry


class InMemoryTraceStore:
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], list[TraceEntry]] = {}

    def add(self, entry: TraceEntry) -> None:
        self._entries.setdefault((entry.firm_id, entry.production_id), []).append(entry)

    def list_for_production(self, firm_id: str, production_id: str) -> list[TraceEntry]:
        return list(self._entries.get((firm_id, production_id), []))
