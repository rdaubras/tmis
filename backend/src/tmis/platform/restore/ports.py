from typing import Protocol

from tmis.platform.restore.schemas import RestorePlan


class RestoreEnginePort(Protocol):
    """Port implemented by every interchangeable restore engine."""

    def dry_run(self, backup_id: str) -> RestorePlan: ...

    def restore(self, backup_id: str) -> dict[str, bytes]: ...
