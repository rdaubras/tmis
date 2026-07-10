from tmis.collaboration.audit.schemas import AuditEntry


class InMemoryAuditStore:
    """Implements `AuditStorePort` — append-only: entries are never
    updated or removed once recorded."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def save(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def list_for_workspace(self, workspace_id: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.workspace_id == workspace_id]

    def list_for_target(self, target_type: str, target_id: str) -> list[AuditEntry]:
        return [
            e for e in self._entries if e.target_type == target_type and e.target_id == target_id
        ]
