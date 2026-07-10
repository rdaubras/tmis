from typing import Protocol

from tmis.collaboration.timeline.schemas import TimelineEntry


class TimelineServicePort(Protocol):
    """Port implemented by every interchangeable timeline service."""

    def for_target(self, target_type: str, target_id: str) -> list[TimelineEntry]: ...

    def for_workspace(self, workspace_id: str) -> list[TimelineEntry]: ...
