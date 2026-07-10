import shutil
from pathlib import Path

import pytest

from tmis.platform.backup.engine import BackupEngine
from tmis.platform.backup.local_storage import LocalFilesystemBackupStorage
from tmis.platform.backup.store import InMemoryBackupRecordStore
from tmis.platform.disaster_recovery.engine import DisasterRecoveryEngine
from tmis.platform.disaster_recovery.schemas import RecoveryObjective
from tmis.platform.restore.engine import RestoreEngine


@pytest.fixture
def backup_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "backups"
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


def _engines(backup_dir: Path) -> tuple[BackupEngine, RestoreEngine]:
    storage = LocalFilesystemBackupStorage(backup_dir)
    records = InMemoryBackupRecordStore()
    return BackupEngine(storage, records), RestoreEngine(storage, records)


def test_full_backup_writes_every_file_and_verifies(backup_dir: Path) -> None:
    backup, _ = _engines(backup_dir)

    record = backup.create_full_backup("firm-1", {"a.txt": b"hello", "b.txt": b"world"})

    assert {e.path for e in record.entries} == {"a.txt", "b.txt"}
    assert backup.verify_integrity(record.id) is True


def test_incremental_backup_only_stores_changed_files(backup_dir: Path) -> None:
    backup, _ = _engines(backup_dir)
    full = backup.create_full_backup("firm-1", {"a.txt": b"hello", "b.txt": b"world"})

    incremental = backup.create_incremental_backup(
        "firm-1", full.id, {"a.txt": b"hello", "b.txt": b"WORLD2", "c.txt": b"new"}
    )

    assert {e.path for e in incremental.entries} == {"b.txt", "c.txt"}


def test_restore_resolves_the_full_chain_including_incrementals(backup_dir: Path) -> None:
    backup, restore = _engines(backup_dir)
    full = backup.create_full_backup("firm-1", {"a.txt": b"hello", "b.txt": b"world"})
    incremental = backup.create_incremental_backup(
        "firm-1", full.id, {"a.txt": b"hello", "b.txt": b"WORLD2", "c.txt": b"new"}
    )

    restored = restore.restore(incremental.id)

    assert restored == {"a.txt": b"hello", "b.txt": b"WORLD2", "c.txt": b"new"}


def test_dry_run_reports_the_plan_without_reading_bytes(backup_dir: Path) -> None:
    backup, restore = _engines(backup_dir)
    record = backup.create_full_backup("firm-1", {"a.txt": b"hello"})

    plan = restore.dry_run(record.id)

    assert plan.files == ["a.txt"]
    assert plan.total_size_bytes == 5


def test_verify_integrity_detects_corruption_on_disk(backup_dir: Path) -> None:
    backup, _ = _engines(backup_dir)
    record = backup.create_full_backup("firm-1", {"a.txt": b"hello"})
    corrupted_path = backup_dir / record.entries[0].storage_key
    corrupted_path.write_bytes(b"corrupted!")

    assert backup.verify_integrity(record.id) is False


def test_restore_raises_on_checksum_mismatch(backup_dir: Path) -> None:
    backup, restore = _engines(backup_dir)
    record = backup.create_full_backup("firm-1", {"a.txt": b"hello"})
    corrupted_path = backup_dir / record.entries[0].storage_key
    corrupted_path.write_bytes(b"corrupted!")

    with pytest.raises(ValueError, match="checksum mismatch"):
        restore.restore(record.id)


def test_incremental_backup_rejects_an_unknown_base(backup_dir: Path) -> None:
    backup, _ = _engines(backup_dir)

    with pytest.raises(ValueError, match="not found"):
        backup.create_incremental_backup("firm-1", "does-not-exist", {"a.txt": b"x"})


def test_disaster_recovery_reports_the_configured_objective() -> None:
    dr = DisasterRecoveryEngine(RecoveryObjective(rto_minutes=30, rpo_minutes=5))

    assert dr.plan() == RecoveryObjective(rto_minutes=30, rpo_minutes=5)


def test_disaster_recovery_does_not_failover_within_the_heartbeat_threshold() -> None:
    dr = DisasterRecoveryEngine(RecoveryObjective(rto_minutes=60, rpo_minutes=15))

    decision = dr.decide_failover(seconds_since_last_heartbeat=10, threshold_seconds=30)

    assert decision.should_failover is False


def test_disaster_recovery_triggers_failover_past_the_heartbeat_threshold() -> None:
    dr = DisasterRecoveryEngine(RecoveryObjective(rto_minutes=60, rpo_minutes=15))

    decision = dr.decide_failover(seconds_since_last_heartbeat=120, threshold_seconds=30)

    assert decision.should_failover is True
    assert "120" in decision.reason
