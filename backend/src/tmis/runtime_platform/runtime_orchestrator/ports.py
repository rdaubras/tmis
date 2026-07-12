from typing import Protocol

from tmis.runtime_platform.runtime_orchestrator.schemas import RuntimeTask


class RuntimeTaskStorePort(Protocol):
    def save(self, task: RuntimeTask) -> None: ...

    def get(self, task_id: str) -> RuntimeTask | None: ...

    def all(self) -> list[RuntimeTask]: ...
