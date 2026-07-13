from tmis.cloud_operations.retention.schemas import (
    ObservabilityDataCategory,
    ObservabilityRetentionPolicy,
)


class InMemoryObservabilityRetentionPolicyStore:
    def __init__(self) -> None:
        self._policies: dict[ObservabilityDataCategory, ObservabilityRetentionPolicy] = {}

    def save(self, policy: ObservabilityRetentionPolicy) -> None:
        self._policies[policy.category] = policy

    def get(self, category: ObservabilityDataCategory) -> ObservabilityRetentionPolicy | None:
        return self._policies.get(category)
