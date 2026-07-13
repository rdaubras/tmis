from tmis.runtime_platform.disaster_recovery.schemas import BackupPolicy


class InMemoryBackupPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[str, BackupPolicy] = {}

    def save(self, policy: BackupPolicy) -> None:
        self._policies[policy.firm_id] = policy

    def get(self, firm_id: str) -> BackupPolicy | None:
        return self._policies.get(firm_id)
