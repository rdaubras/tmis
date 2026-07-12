from typing import Protocol

from tmis.identity_platform.audit.schemas import SecurityAuditEntry


class SecurityAuditStorePort(Protocol):
    def append(self, entry: SecurityAuditEntry) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[SecurityAuditEntry]: ...
