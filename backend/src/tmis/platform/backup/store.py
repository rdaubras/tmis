from tmis.platform.backup.schemas import BackupRecord


class InMemoryBackupRecordStore:
    def __init__(self) -> None:
        self._records: dict[str, BackupRecord] = {}

    def save(self, record: BackupRecord) -> None:
        self._records[record.id] = record

    def get(self, backup_id: str) -> BackupRecord | None:
        return self._records.get(backup_id)

    def list_for_firm(self, firm_id: str) -> list[BackupRecord]:
        return [r for r in self._records.values() if r.firm_id == firm_id]
