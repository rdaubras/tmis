from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


@dataclass(frozen=True, slots=True)
class BackupManifestEntry:
    """One file captured by a backup. `checksum` is a sha256 hex
    digest, used both to detect which files changed since the base
    backup (incremental) and to verify integrity on restore."""

    path: str
    checksum: str
    size_bytes: int
    storage_key: str


@dataclass(slots=True)
class BackupRecord:
    id: str
    firm_id: str
    type: BackupType
    created_at: datetime
    entries: list[BackupManifestEntry] = field(default_factory=list)
    base_backup_id: str | None = None
