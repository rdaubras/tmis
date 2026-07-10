from pathlib import Path


class LocalFilesystemBackupStorage:
    """Reference `BackupStoragePort` implementation writing to a local
    directory. Production deployments swap this for an S3/GCS-backed
    adapter without touching `BackupEngine` (storage-agnostic by
    design, see docs/47-guide-securite-entreprise.md — Backup)."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def write_object(self, key: str, data: bytes) -> None:
        path = self._base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_object(self, key: str) -> bytes:
        return (self._base_dir / key).read_bytes()
