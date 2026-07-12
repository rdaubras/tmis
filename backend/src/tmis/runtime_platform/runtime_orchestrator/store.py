from tmis.runtime_platform.runtime_orchestrator.schemas import RuntimeTask


class InMemoryRuntimeTaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, RuntimeTask] = {}

    def save(self, task: RuntimeTask) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: str) -> RuntimeTask | None:
        return self._tasks.get(task_id)

    def all(self) -> list[RuntimeTask]:
        return list(self._tasks.values())
