import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from tmis.runtime_platform.runtime_orchestrator.ports import RuntimeTaskStorePort
from tmis.runtime_platform.runtime_orchestrator.schemas import RuntimeTask, RuntimeTaskStatus

TaskRunner = Callable[[int], Awaitable[None]]


class RuntimeOrchestrator:
    """Central execution engine for long-running tasks across any
    bounded context. `workflow_automation.execution_engine.
    ExecutionEngine` already sequences a *workflow's own* steps, and
    `ai_team.coordinator.CoordinatorEngine` already sequences a
    *mission's own* sub-tasks — both confirmed by the Sprint 23
    Phase 1 audit to support only a single-level dependency check and
    no cross-context parallelism cap. This engine sits one level
    above: it schedules arbitrary `RuntimeTask`s (which may each wrap
    a whole workflow execution, a mission, or any other long
    operation) by priority and dependency, under one shared
    concurrency limit, with real `asyncio.Task` cancellation and a
    checkpoint-based resume — capabilities none of the
    per-bounded-context engines provide today. A caller building a
    workflow-shaped task passes a `runner` that delegates to
    `ExecutionEngine.resume`, reusing the Workflow Engine rather than
    reimplementing step execution here."""

    def __init__(self, store: RuntimeTaskStorePort, max_parallelism: int = 4) -> None:
        self._store = store
        self._semaphore = asyncio.Semaphore(max_parallelism)
        self._running: dict[str, asyncio.Task[None]] = {}

    def submit(self, task: RuntimeTask) -> None:
        self._store.save(task)

    def get(self, task_id: str) -> RuntimeTask | None:
        return self._store.get(task_id)

    def all(self) -> list[RuntimeTask]:
        return self._store.all()

    def ready_tasks(self) -> list[RuntimeTask]:
        """Tasks whose dependencies are all `DONE`, ordered by
        priority (descending) then submission time — the scheduling
        contract a poller should follow."""
        tasks = self._store.all()
        done_ids = {t.id for t in tasks if t.status is RuntimeTaskStatus.DONE}
        candidates = [
            t
            for t in tasks
            if t.status is RuntimeTaskStatus.PENDING and t.depends_on <= done_ids
        ]
        candidates.sort(key=lambda t: (-t.priority, t.created_at))
        return candidates

    async def run(self, task_id: str, runner: TaskRunner) -> RuntimeTask:
        task = self._store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        async with self._semaphore:
            task.status = RuntimeTaskStatus.RUNNING
            task.started_at = datetime.now(UTC)
            self._store.save(task)
            asyncio_task = asyncio.ensure_future(runner(task.checkpoint))
            self._running[task_id] = asyncio_task
            try:
                await asyncio_task
            except asyncio.CancelledError:
                task.status = RuntimeTaskStatus.CANCELLED
                task.completed_at = datetime.now(UTC)
            except Exception as exc:  # noqa: BLE001 - task failure is data, not a bug here
                task.status = RuntimeTaskStatus.FAILED
                task.error = str(exc)
                task.completed_at = datetime.now(UTC)
            else:
                task.status = RuntimeTaskStatus.DONE
                task.completed_at = datetime.now(UTC)
            finally:
                self._running.pop(task_id, None)
                self._store.save(task)
            return task

    def cancel(self, task_id: str) -> bool:
        """Cancels an in-flight `asyncio.Task` via real cancellation,
        or marks a not-yet-started task `CANCELLED` directly."""
        running = self._running.get(task_id)
        if running is not None:
            running.cancel()
            return True
        task = self._store.get(task_id)
        if task is not None and task.status is RuntimeTaskStatus.PENDING:
            task.status = RuntimeTaskStatus.CANCELLED
            task.completed_at = datetime.now(UTC)
            self._store.save(task)
            return True
        return False

    def checkpoint(self, task_id: str, progress: int) -> None:
        """Lets a long-running `runner` record how far it got, so a
        subsequent `resume()` can pick up from there instead of
        restarting from zero."""
        task = self._store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        task.checkpoint = progress
        self._store.save(task)

    async def resume(self, task_id: str, runner: TaskRunner) -> RuntimeTask:
        task = self._store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        task.status = RuntimeTaskStatus.PENDING
        self._store.save(task)
        return await self.run(task_id, runner)
