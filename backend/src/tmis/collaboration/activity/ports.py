from datetime import datetime
from typing import Protocol

from tmis.collaboration.activity.schemas import ActivityEntry, ActivityType


class ActivityStorePort(Protocol):
    def save(self, entry: ActivityEntry) -> None: ...

    def list_for_workspace(self, workspace_id: str) -> list[ActivityEntry]: ...

    def list_all(self) -> list[ActivityEntry]: ...


class ActivityFeedPort(Protocol):
    """Port implemented by every interchangeable activity feed."""

    def record(
        self,
        workspace_id: str,
        actor_id: str,
        activity_type: ActivityType,
        target_type: str,
        target_id: str,
        summary: str,
        metadata: dict[str, str] | None = None,
    ) -> ActivityEntry: ...

    def query(
        self,
        workspace_id: str,
        activity_type: ActivityType | None = None,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ActivityEntry]: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[ActivityEntry]: ...
