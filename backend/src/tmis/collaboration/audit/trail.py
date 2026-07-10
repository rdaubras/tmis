import uuid
from datetime import UTC, datetime

from tmis.collaboration.audit.ports import AuditStorePort
from tmis.collaboration.audit.schemas import AuditEntry


class AuditTrail:
    """Implements `AuditTrailPort`: the compliance-grade record of every
    action in a workspace — actor, timestamp, IP address (if available),
    action name, and the before/after state (see
    docs/33-legal-collaboration.md — Audit Engine). Distinct from the
    `ActivityFeed`: the feed is a human-readable chronological journal,
    the audit trail is the detailed state-change record behind it."""

    def __init__(self, store: AuditStorePort) -> None:
        self._store = store

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
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            old_state=dict(old_state) if old_state else None,
            new_state=dict(new_state) if new_state else None,
            occurred_at=datetime.now(UTC),
            metadata=dict(metadata) if metadata else {},
        )
        self._store.save(entry)
        return entry

    def list_for_workspace(self, workspace_id: str) -> list[AuditEntry]:
        return self._store.list_for_workspace(workspace_id)

    def list_for_target(self, target_type: str, target_id: str) -> list[AuditEntry]:
        return self._store.list_for_target(target_type, target_id)
