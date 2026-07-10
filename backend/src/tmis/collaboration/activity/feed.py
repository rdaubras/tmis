import uuid
from datetime import UTC, datetime

from tmis.collaboration.activity.ports import ActivityStorePort
from tmis.collaboration.activity.schemas import ActivityEntry, ActivityType


class ActivityFeed:
    """Implements `ActivityFeedPort`: the chronological, filterable
    journal of everything that happens in a workspace — imports,
    modifications, comments, validations, tasks, and AI research/
    generation events (see docs/33-legal-collaboration.md — Activity
    Feed). Append-only; filtering never mutates the underlying log."""

    def __init__(self, store: ActivityStorePort) -> None:
        self._store = store

    def record(
        self,
        workspace_id: str,
        actor_id: str,
        activity_type: ActivityType,
        target_type: str,
        target_id: str,
        summary: str,
        metadata: dict[str, str] | None = None,
    ) -> ActivityEntry:
        entry = ActivityEntry(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            actor_id=actor_id,
            activity_type=activity_type,
            target_type=target_type,
            target_id=target_id,
            summary=summary,
            occurred_at=datetime.now(UTC),
            metadata=dict(metadata) if metadata else {},
        )
        self._store.save(entry)
        return entry

    def query(
        self,
        workspace_id: str,
        activity_type: ActivityType | None = None,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ActivityEntry]:
        entries = self._store.list_for_workspace(workspace_id)
        if activity_type is not None:
            entries = [e for e in entries if e.activity_type == activity_type]
        if actor_id is not None:
            entries = [e for e in entries if e.actor_id == actor_id]
        if target_type is not None:
            entries = [e for e in entries if e.target_type == target_type]
        if target_id is not None:
            entries = [e for e in entries if e.target_id == target_id]
        if since is not None:
            entries = [e for e in entries if e.occurred_at >= since]
        if until is not None:
            entries = [e for e in entries if e.occurred_at <= until]
        return sorted(entries, key=lambda e: e.occurred_at)

    def list_for_target(self, target_type: str, target_id: str) -> list[ActivityEntry]:
        entries = [
            e
            for e in self._store.list_all()
            if e.target_type == target_type and e.target_id == target_id
        ]
        return sorted(entries, key=lambda e: e.occurred_at)
