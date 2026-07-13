from tmis.cloud_operations.logging.schemas import LogRetentionCategory, LogRetentionPolicy


class InMemoryLogRetentionPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[LogRetentionCategory, LogRetentionPolicy] = {}

    def save(self, policy: LogRetentionPolicy) -> None:
        self._policies[policy.category] = policy

    def get(self, category: LogRetentionCategory) -> LogRetentionPolicy | None:
        return self._policies.get(category)

    def list_all(self) -> list[LogRetentionPolicy]:
        return list(self._policies.values())
