import hashlib

from tmis.platform.backup.ports import BackupRecordStorePort, BackupStoragePort
from tmis.platform.backup.schemas import BackupManifestEntry, BackupRecord
from tmis.platform.restore.schemas import RestorePlan


def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RestoreEngine:
    """Implements `RestoreEnginePort` (see
    docs/47-guide-securite-entreprise.md — Disaster Recovery).
    Resolves an incremental backup's full file set by walking its
    `base_backup_id` chain back to the originating full backup,
    applying each generation's changed entries in order so the most
    recent version of every file wins."""

    def __init__(self, storage: BackupStoragePort, record_store: BackupRecordStorePort) -> None:
        self._storage = storage
        self._records = record_store

    def _resolve_manifest(self, backup_id: str) -> dict[str, BackupManifestEntry]:
        chain: list[BackupRecord] = []
        current_id: str | None = backup_id
        while current_id is not None:
            record = self._records.get(current_id)
            if record is None:
                raise ValueError(f"backup {current_id} not found")
            chain.append(record)
            current_id = record.base_backup_id
        manifest: dict[str, BackupManifestEntry] = {}
        for record in reversed(chain):
            for entry in record.entries:
                manifest[entry.path] = entry
        return manifest

    def dry_run(self, backup_id: str) -> RestorePlan:
        manifest = self._resolve_manifest(backup_id)
        return RestorePlan(
            backup_id=backup_id,
            files=sorted(manifest.keys()),
            total_size_bytes=sum(entry.size_bytes for entry in manifest.values()),
        )

    def restore(self, backup_id: str) -> dict[str, bytes]:
        manifest = self._resolve_manifest(backup_id)
        restored: dict[str, bytes] = {}
        for path, entry in manifest.items():
            data = self._storage.read_object(entry.storage_key)
            if _checksum(data) != entry.checksum:
                raise ValueError(f"checksum mismatch restoring {path} (backup {backup_id})")
            restored[path] = data
        return restored
