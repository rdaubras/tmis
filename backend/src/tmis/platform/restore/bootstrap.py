from functools import lru_cache

from tmis.platform.backup.bootstrap import get_backup_record_store, get_backup_storage
from tmis.platform.restore.engine import RestoreEngine


@lru_cache
def get_restore_engine() -> RestoreEngine:
    """Process-wide `RestoreEngine` singleton — see
    docs/47-guide-securite-entreprise.md. Shares the same storage
    backend and manifest store singletons as `get_backup_engine()` so
    a restore always resolves against exactly what was backed up."""
    return RestoreEngine(get_backup_storage(), get_backup_record_store())
