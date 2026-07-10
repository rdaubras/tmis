from tmis.collaboration.activity.ports import ActivityFeedPort
from tmis.collaboration.timeline.schemas import TimelineEntry


class TimelineService:
    """Implements `TimelineServicePort`: a read-model projection of the
    `ActivityFeed`, ordered chronologically for a single target (a
    dossier, a document, a task...) or for a whole workspace (see
    docs/33-legal-collaboration.md — Timeline). Stores nothing of its
    own — the activity feed remains the single source of truth."""

    def __init__(self, activity_feed: ActivityFeedPort) -> None:
        self._activity_feed = activity_feed

    def for_target(self, target_type: str, target_id: str) -> list[TimelineEntry]:
        entries = self._activity_feed.list_for_target(target_type, target_id)
        return [
            TimelineEntry(
                activity_type=e.activity_type,
                actor_id=e.actor_id,
                summary=e.summary,
                occurred_at=e.occurred_at,
            )
            for e in entries
        ]

    def for_workspace(self, workspace_id: str) -> list[TimelineEntry]:
        entries = self._activity_feed.query(workspace_id)
        return [
            TimelineEntry(
                activity_type=e.activity_type,
                actor_id=e.actor_id,
                summary=e.summary,
                occurred_at=e.occurred_at,
            )
            for e in entries
        ]
