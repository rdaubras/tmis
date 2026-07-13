from typing import Protocol

from tmis.runtime_platform.high_availability.schemas import NodeHeartbeat


class NodeHeartbeatStorePort(Protocol):
    def record(self, heartbeat: NodeHeartbeat) -> None: ...

    def get(self, node_id: str) -> NodeHeartbeat | None: ...

    def all(self) -> list[NodeHeartbeat]: ...
