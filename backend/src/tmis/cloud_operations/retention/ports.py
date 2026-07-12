from typing import Protocol

from tmis.cloud_operations.retention.schemas import (
    ObservabilityDataCategory,
    ObservabilityRetentionPolicy,
)


class ObservabilityRetentionPolicyStorePort(Protocol):
    def save(self, policy: ObservabilityRetentionPolicy) -> None: ...

    def get(self, category: ObservabilityDataCategory) -> ObservabilityRetentionPolicy | None: ...
