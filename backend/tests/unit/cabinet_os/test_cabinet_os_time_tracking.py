import pytest

from tmis.cabinet_os.time_tracking.schemas import ActivityType, EntryMethod
from tmis.cabinet_os.time_tracking.service import TimeTrackingService


def test_log_creates_a_complete_manual_entry() -> None:
    service = TimeTrackingService()
    entry = service.log("firm-1", "collab-1", "case-1", 45, ActivityType.RESEARCH)

    assert entry.entry_method is EntryMethod.MANUAL
    assert entry.duration_minutes == 45
    assert entry.ended_at is not None


def test_start_timer_leaves_duration_unset() -> None:
    service = TimeTrackingService()
    entry = service.start_timer("firm-1", "collab-1", "case-1", ActivityType.DRAFTING)

    assert entry.entry_method is EntryMethod.TIMER
    assert entry.duration_minutes is None
    assert entry.ended_at is None


def test_stop_timer_computes_duration() -> None:
    service = TimeTrackingService()
    entry = service.start_timer("firm-1", "collab-1", "case-1", ActivityType.DRAFTING)

    stopped = service.stop_timer(entry.id)

    assert stopped.duration_minutes is not None
    assert stopped.duration_minutes >= 0
    assert stopped.ended_at is not None


def test_stop_timer_twice_raises() -> None:
    service = TimeTrackingService()
    entry = service.start_timer("firm-1", "collab-1", "case-1", ActivityType.DRAFTING)
    service.stop_timer(entry.id)

    with pytest.raises(ValueError, match="is not running"):
        service.stop_timer(entry.id)


def test_stop_unknown_timer_raises() -> None:
    service = TimeTrackingService()
    with pytest.raises(ValueError, match="Unknown time entry"):
        service.stop_timer("nope")


def test_total_minutes_for_case_sums_across_entries() -> None:
    service = TimeTrackingService()
    service.log("firm-1", "collab-1", "case-1", 30, ActivityType.RESEARCH)
    service.log("firm-1", "collab-2", "case-1", 15, ActivityType.CALL)
    service.log("firm-1", "collab-1", "case-2", 100, ActivityType.RESEARCH)

    assert service.total_minutes_for_case("case-1") == 45


def test_list_for_collaborator_filters_correctly() -> None:
    service = TimeTrackingService()
    service.log("firm-1", "collab-1", "case-1", 30, ActivityType.RESEARCH)
    service.log("firm-1", "collab-2", "case-1", 15, ActivityType.CALL)

    entries = service.list_for_collaborator("collab-1")

    assert len(entries) == 1
    assert entries[0].collaborator_id == "collab-1"


def test_non_billable_entry_defaults_to_billable_true() -> None:
    service = TimeTrackingService()
    entry = service.log(
        "firm-1", "collab-1", "case-1", 30, ActivityType.ADMINISTRATIVE, billable=False
    )

    assert entry.billable is False
