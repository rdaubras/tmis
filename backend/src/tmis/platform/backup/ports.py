from typing import Protocol

from tmis.platform.backup.schemas import BackupRecord


class BackupStoragePort(Protocol):
    """Storage-agnostic object sink — a local filesystem, S3, GCS, or
    any blob store can implement this without the backup engine
    knowing which (see docs/47-guide-securite-entreprise.md —
    Backup)."""

    def write_object(self, key: str, data: bytes) -> None: ...

    def read_object(self, key: str) -> bytes: ...


class BackupRecordStorePort(Protocol):
    def save(self, record: BackupRecord) -> None: ...

    def get(self, backup_id: str) -> BackupRecord | None: ...

    def list_for_firm(self, firm_id: str) -> list[BackupRecord]: ...


class BackupEnginePort(Protocol):
    """Port implemented by every interchangeable backup engine."""

    def create_full_backup(self, firm_id: str, files: dict[str, bytes]) -> BackupRecord: ...

    def create_incremental_backup(
        self, firm_id: str, base_backup_id: str, files: dict[str, bytes]
    ) -> BackupRecord: ...

    def verify_integrity(self, backup_id: str) -> bool: ...
