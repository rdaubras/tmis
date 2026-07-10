import hashlib
import uuid
from datetime import UTC, datetime

from tmis.platform.backup.ports import BackupRecordStorePort, BackupStoragePort
from tmis.platform.backup.schemas import BackupManifestEntry, BackupRecord, BackupType


def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BackupEngine:
    """Implements `BackupEnginePort` (see
    docs/47-guide-securite-entreprise.md — Backup). Storage-agnostic:
    depends only on `BackupStoragePort`, so swapping the local
    filesystem adapter for S3/GCS requires no change here.

    An incremental backup only writes files whose checksum changed
    relative to its `base_backup_id` manifest — unchanged files are
    omitted and resolved by walking the chain back to the full backup
    at restore time (see `tmis.platform.restore.engine`)."""

    def __init__(self, storage: BackupStoragePort, record_store: BackupRecordStorePort) -> None:
        self._storage = storage
        self._records = record_store

    def create_full_backup(self, firm_id: str, files: dict[str, bytes]) -> BackupRecord:
        backup_id = str(uuid.uuid4())
        entries = [
            self._write_entry(firm_id, backup_id, path, data) for path, data in files.items()
        ]
        record = BackupRecord(
            id=backup_id,
            firm_id=firm_id,
            type=BackupType.FULL,
            created_at=datetime.now(UTC),
            entries=entries,
        )
        self._records.save(record)
        return record

    def create_incremental_backup(
        self, firm_id: str, base_backup_id: str, files: dict[str, bytes]
    ) -> BackupRecord:
        base = self._records.get(base_backup_id)
        if base is None:
            raise ValueError(f"base backup {base_backup_id} not found")
        base_checksums = {entry.path: entry.checksum for entry in base.entries}
        backup_id = str(uuid.uuid4())
        entries = [
            self._write_entry(firm_id, backup_id, path, data)
            for path, data in files.items()
            if base_checksums.get(path) != _checksum(data)
        ]
        record = BackupRecord(
            id=backup_id,
            firm_id=firm_id,
            type=BackupType.INCREMENTAL,
            created_at=datetime.now(UTC),
            entries=entries,
            base_backup_id=base_backup_id,
        )
        self._records.save(record)
        return record

    def verify_integrity(self, backup_id: str) -> bool:
        record = self._records.get(backup_id)
        if record is None:
            return False
        return all(
            _checksum(self._storage.read_object(entry.storage_key)) == entry.checksum
            for entry in record.entries
        )

    def _write_entry(
        self, firm_id: str, backup_id: str, path: str, data: bytes
    ) -> BackupManifestEntry:
        storage_key = f"{firm_id}/{backup_id}/{path}"
        self._storage.write_object(storage_key, data)
        return BackupManifestEntry(
            path=path, checksum=_checksum(data), size_bytes=len(data), storage_key=storage_key
        )
