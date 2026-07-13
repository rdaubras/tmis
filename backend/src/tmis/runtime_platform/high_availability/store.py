from tmis.runtime_platform.high_availability.schemas import NodeHeartbeat


class InMemoryNodeHeartbeatStore:
    def __init__(self) -> None:
        self._heartbeats: dict[str, NodeHeartbeat] = {}

    def record(self, heartbeat: NodeHeartbeat) -> None:
        self._heartbeats[heartbeat.node_id] = heartbeat

    def get(self, node_id: str) -> NodeHeartbeat | None:
        return self._heartbeats.get(node_id)

    def all(self) -> list[NodeHeartbeat]:
        return list(self._heartbeats.values())
