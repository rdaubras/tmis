from tmis.ai_governance.audit.schemas import AIAuditEntry


class InMemoryAIAuditStore:
    def __init__(self) -> None:
        self._entries: list[AIAuditEntry] = []

    def add(self, entry: AIAuditEntry) -> None:
        self._entries.append(entry)

    def list_for_firm(self, firm_id: str) -> list[AIAuditEntry]:
        return [e for e in self._entries if e.firm_id == firm_id]

    def list_for_production(self, firm_id: str, production_id: str) -> list[AIAuditEntry]:
        return [
            e for e in self._entries if e.firm_id == firm_id and e.production_id == production_id
        ]
