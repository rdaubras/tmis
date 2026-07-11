import time

from tmis.ai.schemas.agent import AgentOutput
from tmis.ai_team.work_queue.engine import InMemoryWorkQueue
from tmis.ai_team.work_queue.schemas import WorkItem, WorkItemStatus


def test_dequeue_next_picks_highest_priority_first() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="low", sub_task_id="st-1", agent_id="a1", priority=1))
    queue.enqueue(WorkItem(id="high", sub_task_id="st-2", agent_id="a1", priority=5))

    assert queue.dequeue_next().id == "high"  # type: ignore[union-attr]


def test_dequeue_next_does_not_mutate_status() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1"))

    item = queue.dequeue_next()

    assert item is not None
    assert item.status is WorkItemStatus.PENDING


def test_mark_running_increments_attempts_and_sets_started_at() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1"))

    queue.mark_running("a")

    item = queue.get("a")
    assert item is not None
    assert item.status is WorkItemStatus.RUNNING
    assert item.attempts == 1
    assert item.started_at is not None


def test_mark_done_stores_the_result() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1"))
    queue.mark_running("a")

    output = AgentOutput(result={"text": "done"})
    queue.mark_done("a", output)

    item = queue.get("a")
    assert item is not None
    assert item.status is WorkItemStatus.DONE
    assert item.result is output


def test_mark_failed_retries_until_max_attempts_then_fails() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1", max_attempts=2))

    queue.mark_running("a")
    after_first = queue.mark_failed("a", "boom")
    assert after_first.status is WorkItemStatus.RETRYING

    queue.mark_running("a")
    after_second = queue.mark_failed("a", "boom again")
    assert after_second.status is WorkItemStatus.FAILED
    assert after_second.completed_at is not None


def test_cancel_sets_terminal_status() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1"))

    queue.cancel("a")

    item = queue.get("a")
    assert item is not None
    assert item.status is WorkItemStatus.CANCELLED


def test_check_timeouts_retries_when_attempts_remain() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1", timeout_seconds=0.01))
    queue.mark_running("a")
    time.sleep(0.03)

    timed_out = queue.check_timeouts()

    assert [i.id for i in timed_out] == ["a"]
    assert queue.get("a").status is WorkItemStatus.RETRYING  # type: ignore[union-attr]


def test_check_timeouts_marks_timed_out_when_attempts_exhausted() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(
        WorkItem(id="a", sub_task_id="st-1", agent_id="a1", max_attempts=1, timeout_seconds=0.01)
    )
    queue.mark_running("a")
    time.sleep(0.03)

    queue.check_timeouts()

    assert queue.get("a").status is WorkItemStatus.TIMED_OUT  # type: ignore[union-attr]


def test_check_timeouts_ignores_items_within_their_budget() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1", timeout_seconds=60))
    queue.mark_running("a")

    assert queue.check_timeouts() == []


def test_list_all_returns_every_item() -> None:
    queue = InMemoryWorkQueue()
    queue.enqueue(WorkItem(id="a", sub_task_id="st-1", agent_id="a1"))
    queue.enqueue(WorkItem(id="b", sub_task_id="st-2", agent_id="a1"))

    assert len(queue.list_all()) == 2
