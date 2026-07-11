from typing import Protocol

from tmis.ai_governance.audit.schemas import AIAuditEntry


class AIAuditStorePort(Protocol):
    def add(self, entry: AIAuditEntry) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[AIAuditEntry]: ...

    def list_for_production(self, firm_id: str, production_id: str) -> list[AIAuditEntry]: ...
