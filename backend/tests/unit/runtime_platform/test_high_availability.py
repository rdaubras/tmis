from datetime import UTC, datetime, timedelta

from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.disaster_recovery.schemas import RecoveryObjective
from tmis.runtime_platform.high_availability.engine import HighAvailabilityEngine
from tmis.runtime_platform.high_availability.schemas import NodeStatus
from tmis.runtime_platform.high_availability.store import InMemoryNodeHeartbeatStore


def _engine() -> HighAvailabilityEngine:
    disaster_recovery = DisasterRecoveryEngine(RecoveryObjective(rto_minutes=60, rpo_minutes=15))
    return HighAvailabilityEngine(
        disaster_recovery,
        InMemoryNodeHeartbeatStore(),
        suspect_threshold_seconds=10,
        down_threshold_seconds=30,
    )


def test_unknown_node_is_down() -> None:
    engine = _engine()
    assert engine.node_status("ghost") is NodeStatus.DOWN


def test_recent_heartbeat_is_healthy() -> None:
    engine = _engine()
    engine.heartbeat("node-1")
    assert engine.node_status("node-1") is NodeStatus.HEALTHY


def test_stale_heartbeat_becomes_suspect_then_down() -> None:
    engine = _engine()
    engine.heartbeat("node-1")

    suspect_time = datetime.now(UTC) + timedelta(seconds=15)
    assert engine.node_status("node-1", now=suspect_time) is NodeStatus.SUSPECT

    down_time = datetime.now(UTC) + timedelta(seconds=35)
    assert engine.node_status("node-1", now=down_time) is NodeStatus.DOWN


def test_supervise_reports_status_for_every_known_node() -> None:
    engine = _engine()
    engine.heartbeat("node-1")
    engine.heartbeat("node-2")

    statuses = engine.supervise()
    assert statuses == {"node-1": NodeStatus.HEALTHY, "node-2": NodeStatus.HEALTHY}


def test_decide_failover_composes_disaster_recovery_engine() -> None:
    engine = _engine()
    engine.heartbeat("node-1")

    far_future = datetime.now(UTC) + timedelta(seconds=60)
    decision = engine.decide_failover("node-1", now=far_future)
    assert decision.should_failover is True


def test_record_and_read_replication_status() -> None:
    engine = _engine()
    engine.record_replication("replica-1", 2.5)
    statuses = engine.replication_status()
    assert len(statuses) == 1
    assert statuses[0].replica_id == "replica-1"
    assert statuses[0].lag_seconds == 2.5
