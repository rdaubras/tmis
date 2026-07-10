from tmis.collaboration.activity.feed import ActivityFeed
from tmis.collaboration.activity.schemas import ActivityType
from tmis.collaboration.activity.store import InMemoryActivityStore
from tmis.collaboration.timeline.service import TimelineService


def _feed() -> ActivityFeed:
    return ActivityFeed(InMemoryActivityStore())


def test_record_and_list_for_workspace() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "Task created")

    entries = feed.query("ws-1")

    assert len(entries) == 1
    assert entries[0].summary == "Task created"


def test_list_is_filterable_by_activity_type() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "Task created")
    feed.record("ws-1", "actor-1", ActivityType.COMMENT, "task", "t1", "Comment added")

    only_comments = feed.query("ws-1", activity_type=ActivityType.COMMENT)

    assert len(only_comments) == 1
    assert only_comments[0].activity_type is ActivityType.COMMENT


def test_list_is_filterable_by_actor_and_target() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "By actor 1")
    feed.record("ws-1", "actor-2", ActivityType.TASK, "task", "t2", "By actor 2")

    for_actor_1 = feed.query("ws-1", actor_id="actor-1")
    for_target_t2 = feed.query("ws-1", target_type="task", target_id="t2")

    assert len(for_actor_1) == 1 and for_actor_1[0].actor_id == "actor-1"
    assert len(for_target_t2) == 1 and for_target_t2[0].target_id == "t2"


def test_query_is_scoped_to_the_workspace() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "In workspace 1")
    feed.record("ws-2", "actor-1", ActivityType.TASK, "task", "t1", "In workspace 2")

    assert len(feed.query("ws-1")) == 1


def test_entries_are_returned_in_chronological_order() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "First")
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "Second")
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "Third")

    entries = feed.query("ws-1")

    assert [e.summary for e in entries] == ["First", "Second", "Third"]


def test_timeline_service_for_target_projects_activity_across_workspaces() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.COMMENT, "case", "case-1", "Commented")
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "Unrelated")
    timeline = TimelineService(feed)

    entries = timeline.for_target("case", "case-1")

    assert len(entries) == 1
    assert entries[0].summary == "Commented"


def test_timeline_service_for_workspace_returns_everything_in_order() -> None:
    feed = _feed()
    feed.record("ws-1", "actor-1", ActivityType.TASK, "task", "t1", "First")
    feed.record("ws-1", "actor-1", ActivityType.COMMENT, "task", "t1", "Second")
    timeline = TimelineService(feed)

    entries = timeline.for_workspace("ws-1")

    assert [e.summary for e in entries] == ["First", "Second"]
