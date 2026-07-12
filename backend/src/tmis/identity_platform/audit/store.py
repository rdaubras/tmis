from tmis.identity_platform.audit.schemas import SecurityAuditEntry


class InMemorySecurityAuditStore:
    def __init__(self) -> None:
        self._entries: list[SecurityAuditEntry] = []

    def append(self, entry: SecurityAuditEntry) -> None:
        self._entries.append(entry)

    def list_for_firm(self, firm_id: str) -> list[SecurityAuditEntry]:
        return [e for e in self._entries if e.firm_id == firm_id]
