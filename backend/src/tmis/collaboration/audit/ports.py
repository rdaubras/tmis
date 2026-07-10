from typing import Protocol

from tmis.collaboration.audit.schemas import AuditEntry


class AuditStorePort(Protocol):
    def save(self, entry: AuditEntry) -> None: ...

    def list_for_workspace(self, workspace_id: str) -> list[AuditEntry]: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[AuditEntry]: ...


class AuditTrailPort(Protocol):
    """Port implemented by every interchangeable audit trail."""

    def record(
        self,
        workspace_id: str,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        old_state: dict[str, str] | None = None,
        new_state: dict[str, str] | None = None,
        ip_address: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> AuditEntry: ...

    def list_for_workspace(self, workspace_id: str) -> list[AuditEntry]: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[AuditEntry]: ...
