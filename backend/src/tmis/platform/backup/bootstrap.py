from functools import lru_cache
from pathlib import Path

from tmis.core.config import get_settings
from tmis.platform.backup.engine import BackupEngine
from tmis.platform.backup.local_storage import LocalFilesystemBackupStorage
from tmis.platform.backup.store import InMemoryBackupRecordStore


@lru_cache
def get_backup_storage() -> LocalFilesystemBackupStorage:
    """Process-wide storage backend singleton, shared between the
    backup and restore engines so they always read/write the same
    location (see docs/47-guide-securite-entreprise.md — Backup).
    Defaults to a project-relative `var/backups` directory rather than
    a shared, world-writable `/tmp` path — production deployments
    should override `TMIS_BACKUP_STORAGE_DIR` to point at a
    dedicated, access-controlled volume."""
    return LocalFilesystemBackupStorage(Path(get_settings().backup_storage_dir))


@lru_cache
def get_backup_record_store() -> InMemoryBackupRecordStore:
    """Process-wide backup manifest store singleton, shared between
    the backup and restore engines."""
    return InMemoryBackupRecordStore()


@lru_cache
def get_backup_engine() -> BackupEngine:
    """Process-wide `BackupEngine` singleton — see
    docs/47-guide-securite-entreprise.md. Production deployments
    should override the storage backend via configuration rather than
    relying on this default local-filesystem location."""
    return BackupEngine(get_backup_storage(), get_backup_record_store())
