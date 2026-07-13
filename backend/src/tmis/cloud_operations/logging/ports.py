from typing import Protocol

from tmis.cloud_operations.logging.schemas import LogRetentionCategory, LogRetentionPolicy


class LogRetentionPolicyStorePort(Protocol):
    def save(self, policy: LogRetentionPolicy) -> None: ...

    def get(self, category: LogRetentionCategory) -> LogRetentionPolicy | None: ...

    def list_all(self) -> list[LogRetentionPolicy]: ...
