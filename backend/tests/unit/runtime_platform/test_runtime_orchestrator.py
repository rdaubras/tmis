import asyncio

import pytest

from tmis.runtime_platform.runtime_orchestrator.engine import RuntimeOrchestrator
from tmis.runtime_platform.runtime_orchestrator.schemas import RuntimeTask, RuntimeTaskStatus
from tmis.runtime_platform.runtime_orchestrator.store import InMemoryRuntimeTaskStore


def _orchestrator(max_parallelism: int = 4) -> RuntimeOrchestrator:
    return RuntimeOrchestrator(InMemoryRuntimeTaskStore(), max_parallelism=max_parallelism)


def test_ready_tasks_respects_dependencies_and_priority() -> None:
    orchestrator = _orchestrator()
    orchestrator.submit(RuntimeTask(id="low", name="low", priority=1))
    orchestrator.submit(RuntimeTask(id="high", name="high", priority=10))
    orchestrator.submit(
        RuntimeTask(id="blocked", name="blocked", depends_on=frozenset({"low"}))
    )

    ready = orchestrator.ready_tasks()
    assert [t.id for t in ready] == ["high", "low"]


async def _noop(_checkpoint: int) -> None:
    await asyncio.sleep(0)


def test_run_marks_task_done_and_unblocks_dependents() -> None:
    async def scenario() -> None:
        orchestrator = _orchestrator()
        orchestrator.submit(RuntimeTask(id="a", name="a"))
        orchestrator.submit(RuntimeTask(id="b", name="b", depends_on=frozenset({"a"})))

        assert [t.id for t in orchestrator.ready_tasks()] == ["a"]
        result = await orchestrator.run("a", _noop)
        assert result.status is RuntimeTaskStatus.DONE
        assert [t.id for t in orchestrator.ready_tasks()] == ["b"]

    asyncio.run(scenario())


def test_run_marks_task_failed_on_exception() -> None:
    async def failing(_checkpoint: int) -> None:
        raise ValueError("boom")

    async def scenario() -> None:
        orchestrator = _orchestrator()
        orchestrator.submit(RuntimeTask(id="a", name="a"))
        result = await orchestrator.run("a", failing)
        assert result.status is RuntimeTaskStatus.FAILED
        assert result.error == "boom"

    asyncio.run(scenario())


def test_cancel_pending_task_marks_cancelled() -> None:
    orchestrator = _orchestrator()
    orchestrator.submit(RuntimeTask(id="a", name="a"))
    assert orchestrator.cancel("a") is True
    assert orchestrator.get("a").status is RuntimeTaskStatus.CANCELLED


def test_cancel_running_task_uses_real_asyncio_cancellation() -> None:
    async def slow(_checkpoint: int) -> None:
        await asyncio.sleep(10)

    async def scenario() -> None:
        orchestrator = _orchestrator()
        orchestrator.submit(RuntimeTask(id="a", name="a"))
        run_task = asyncio.ensure_future(orchestrator.run("a", slow))
        await asyncio.sleep(0)
        assert orchestrator.cancel("a") is True
        result = await run_task
        assert result.status is RuntimeTaskStatus.CANCELLED

    asyncio.run(scenario())


def test_checkpoint_and_resume() -> None:
    async def scenario() -> None:
        orchestrator = _orchestrator()
        orchestrator.submit(RuntimeTask(id="a", name="a"))
        orchestrator.checkpoint("a", 3)
        seen_checkpoints = []

        async def runner(checkpoint: int) -> None:
            seen_checkpoints.append(checkpoint)

        await orchestrator.resume("a", runner)
        assert seen_checkpoints == [3]

    asyncio.run(scenario())


def test_max_parallelism_limits_concurrent_execution() -> None:
    async def scenario() -> None:
        orchestrator = _orchestrator(max_parallelism=1)
        orchestrator.submit(RuntimeTask(id="a", name="a"))
        orchestrator.submit(RuntimeTask(id="b", name="b"))
        concurrent = 0
        max_concurrent = 0

        async def runner(_checkpoint: int) -> None:
            nonlocal concurrent, max_concurrent
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            await asyncio.sleep(0.01)
            concurrent -= 1

        await asyncio.gather(orchestrator.run("a", runner), orchestrator.run("b", runner))
        assert max_concurrent == 1

    asyncio.run(scenario())


def test_run_unknown_task_raises_key_error() -> None:
    async def scenario() -> None:
        orchestrator = _orchestrator()
        with pytest.raises(KeyError):
            await orchestrator.run("missing", _noop)

    asyncio.run(scenario())
