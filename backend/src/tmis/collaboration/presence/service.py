from datetime import UTC, datetime

from tmis.collaboration.presence.schemas import PresenceInfo, PresenceStatus


class InMemoryPresenceTracker:
    """Implements `PresencePort`: reference in-memory heartbeat store.
    No real-time push is implemented — a future websocket/pubsub layer
    would call `heartbeat()` on every client tick and read `list_online`/
    `viewers` to broadcast indicators (see docs/33-legal-collaboration.md
    — Presence Engine)."""

    def __init__(self) -> None:
        self._presence: dict[tuple[str, str], PresenceInfo] = {}

    def heartbeat(
        self,
        workspace_id: str,
        member_id: str,
        status: PresenceStatus,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> PresenceInfo:
        info = PresenceInfo(
            workspace_id=workspace_id,
            member_id=member_id,
            status=status,
            target_type=target_type,
            target_id=target_id,
            last_seen_at=datetime.now(UTC),
        )
        self._presence[(workspace_id, member_id)] = info
        return info

    def list_online(self, workspace_id: str) -> list[PresenceInfo]:
        return [
            info
            for info in self._presence.values()
            if info.workspace_id == workspace_id and info.status is PresenceStatus.ONLINE
        ]

    def viewers(self, target_type: str, target_id: str) -> list[PresenceInfo]:
        return [
            info
            for info in self._presence.values()
            if info.target_type == target_type
            and info.target_id == target_id
            and info.status is not PresenceStatus.OFFLINE
        ]
