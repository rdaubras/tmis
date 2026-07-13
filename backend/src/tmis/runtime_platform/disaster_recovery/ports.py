from typing import Protocol

from tmis.runtime_platform.disaster_recovery.schemas import BackupPolicy


class BackupPolicyStorePort(Protocol):
    def save(self, policy: BackupPolicy) -> None: ...

    def get(self, firm_id: str) -> BackupPolicy | None: ...
