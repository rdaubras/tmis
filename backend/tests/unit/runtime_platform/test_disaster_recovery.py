from datetime import UTC, datetime, timedelta
from pathlib import Path

from tmis.platform.backup.engine import BackupEngine
from tmis.platform.backup.local_storage import LocalFilesystemBackupStorage
from tmis.platform.backup.store import InMemoryBackupRecordStore
from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.disaster_recovery.schemas import RecoveryObjective
from tmis.platform.restore.engine import RestoreEngine
from tmis.runtime_platform.disaster_recovery.engine import RuntimeDisasterRecoveryEngine
from tmis.runtime_platform.disaster_recovery.store import InMemoryBackupPolicyStore


def _engine(tmp_path: Path) -> tuple[RuntimeDisasterRecoveryEngine, BackupEngine]:
    storage = LocalFilesystemBackupStorage(tmp_path)
    records = InMemoryBackupRecordStore()
    backup = BackupEngine(storage, records)
    restore = RestoreEngine(storage, records)
    disaster_recovery = DisasterRecoveryEngine(RecoveryObjective(rto_minutes=60, rpo_minutes=15))
    engine = RuntimeDisasterRecoveryEngine(
        backup, restore, disaster_recovery, InMemoryBackupPolicyStore()
    )
    return engine, backup


def test_set_and_read_backup_policy(tmp_path: Path) -> None:
    engine, _ = _engine(tmp_path)
    policy = engine.set_policy("firm-1", "0 3 * * *", retention_days=90)
    assert policy.retention_days == 90
    assert engine.policy_for("firm-1") is policy
    assert engine.policy_for("firm-unknown") is None


def test_simulate_restore_combines_plan_and_integrity(tmp_path: Path) -> None:
    engine, backup = _engine(tmp_path)
    record = backup.create_full_backup("firm-1", {"contract.pdf": b"hello"})

    result = engine.simulate_restore(record.id)
    assert result.plan.files == ["contract.pdf"]
    assert result.integrity_valid is True


def test_validate_backup_reflects_verify_integrity(tmp_path: Path) -> None:
    engine, backup = _engine(tmp_path)
    record = backup.create_full_backup("firm-1", {"contract.pdf": b"hello"})
    assert engine.validate_backup(record.id) is True
    assert engine.validate_backup("unknown-backup") is False


def test_rpo_rto_estimate_with_no_backup_never_meets_objective(tmp_path: Path) -> None:
    engine, _ = _engine(tmp_path)
    estimate = engine.estimate_rpo_rto(None)
    assert estimate.meets_objective is False
    assert estimate.actual_rpo_minutes is None


def test_rpo_rto_estimate_meets_objective_when_backup_recent(tmp_path: Path) -> None:
    engine, _ = _engine(tmp_path)
    now = datetime.now(UTC)
    recent_backup = now - timedelta(minutes=5)

    estimate = engine.estimate_rpo_rto(recent_backup, now=now)
    assert estimate.meets_objective is True
    assert estimate.actual_rpo_minutes is not None
    assert estimate.actual_rpo_minutes < estimate.rpo_minutes


def test_rpo_rto_estimate_fails_objective_when_backup_stale(tmp_path: Path) -> None:
    engine, _ = _engine(tmp_path)
    now = datetime.now(UTC)
    stale_backup = now - timedelta(minutes=120)

    estimate = engine.estimate_rpo_rto(stale_backup, now=now)
    assert estimate.meets_objective is False
