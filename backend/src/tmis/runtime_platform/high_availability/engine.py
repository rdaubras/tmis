from datetime import UTC, datetime

from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.disaster_recovery.schemas import FailoverDecision
from tmis.runtime_platform.high_availability.ports import NodeHeartbeatStorePort
from tmis.runtime_platform.high_availability.schemas import (
    NodeHeartbeat,
    NodeStatus,
    ReplicationStatus,
)


class HighAvailabilityEngine:
    """Extends `platform.disaster_recovery.DisasterRecoveryEngine`
    (Sprint 10) — which already owns the single heartbeat-threshold
    `decide_failover` decision — with the per-node bookkeeping that
    engine explicitly defers to a caller: recording a heartbeat per
    node, classifying each node HEALTHY/SUSPECT/DOWN, supervising all
    known nodes at once, and tracking replication lag. The actual
    failover mechanics (DNS cutover, pod rescheduling) remain out of
    scope here too, deferred to the Kubernetes manifests exactly as
    `DisasterRecoveryEngine`'s own docstring already states."""

    def __init__(
        self,
        disaster_recovery: DisasterRecoveryEngine,
        heartbeats: NodeHeartbeatStorePort,
        *,
        suspect_threshold_seconds: float = 10.0,
        down_threshold_seconds: float = 30.0,
    ) -> None:
        self._disaster_recovery = disaster_recovery
        self._heartbeats = heartbeats
        self._suspect_threshold_seconds = suspect_threshold_seconds
        self._down_threshold_seconds = down_threshold_seconds
        self._replication: dict[str, ReplicationStatus] = {}

    def heartbeat(self, node_id: str) -> None:
        self._heartbeats.record(NodeHeartbeat(node_id=node_id))

    def node_status(self, node_id: str, *, now: datetime | None = None) -> NodeStatus:
        now = now or datetime.now(UTC)
        beat = self._heartbeats.get(node_id)
        if beat is None:
            return NodeStatus.DOWN
        elapsed = (now - beat.last_heartbeat_at).total_seconds()
        if elapsed >= self._down_threshold_seconds:
            return NodeStatus.DOWN
        if elapsed >= self._suspect_threshold_seconds:
            return NodeStatus.SUSPECT
        return NodeStatus.HEALTHY

    def supervise(self, *, now: datetime | None = None) -> dict[str, NodeStatus]:
        now = now or datetime.now(UTC)
        return {
            beat.node_id: self.node_status(beat.node_id, now=now)
            for beat in self._heartbeats.all()
        }

    def decide_failover(self, node_id: str, *, now: datetime | None = None) -> FailoverDecision:
        now = now or datetime.now(UTC)
        beat = self._heartbeats.get(node_id)
        if beat is None:
            elapsed = float("inf")
        else:
            elapsed = (now - beat.last_heartbeat_at).total_seconds()
        return self._disaster_recovery.decide_failover(elapsed, self._down_threshold_seconds)

    def record_replication(self, replica_id: str, lag_seconds: float) -> ReplicationStatus:
        status = ReplicationStatus(replica_id=replica_id, lag_seconds=lag_seconds)
        self._replication[replica_id] = status
        return status

    def replication_status(self) -> list[ReplicationStatus]:
        return list(self._replication.values())
