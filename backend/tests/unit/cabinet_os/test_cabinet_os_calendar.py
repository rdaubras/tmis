from datetime import UTC, datetime, timedelta

import pytest

from tmis.cabinet_os.calendar.engine import ConfigurableCalendarEngine
from tmis.cabinet_os.calendar.schemas import CalendarEventType, CalendarView
from tmis.cabinet_os.calendar.store import InMemoryCalendarStore
from tmis.cabinet_os.deadlines.engine import ConfigurableDeadlineEngine
from tmis.cabinet_os.deadlines.schemas import DeadlineCandidate, DeadlineStatus
from tmis.cabinet_os.deadlines.store import InMemoryDeadlineStore
from tmis.cabinet_os.hearings.engine import HearingEngine
from tmis.cabinet_os.hearings.store import InMemoryHearingStore


def _calendar() -> ConfigurableCalendarEngine:
    return ConfigurableCalendarEngine(InMemoryCalendarStore())


def test_schedule_and_reschedule_event() -> None:
    engine = _calendar()
    now = datetime(2026, 7, 10, 10, 0, tzinfo=UTC)
    event = engine.schedule("firm-1", CalendarEventType.APPOINTMENT, "RDV", now)

    rescheduled = engine.reschedule(event.id, now + timedelta(hours=1))

    assert rescheduled.starts_at == now + timedelta(hours=1)


def test_cancel_removes_the_event() -> None:
    engine = _calendar()
    now = datetime(2026, 7, 10, 10, 0, tzinfo=UTC)
    event = engine.schedule("firm-1", CalendarEventType.CALL, "Appel", now)

    engine.cancel(event.id)

    assert engine.view("firm-1", CalendarView.AGENDA, now) == []


def test_cancel_unknown_event_raises() -> None:
    engine = _calendar()
    with pytest.raises(ValueError, match="Unknown calendar event"):
        engine.cancel("nope")


def test_day_view_only_returns_events_on_that_day() -> None:
    engine = _calendar()
    day = datetime(2026, 7, 10, 9, 0, tzinfo=UTC)
    engine.schedule("firm-1", CalendarEventType.CALL, "Today", day)
    engine.schedule("firm-1", CalendarEventType.CALL, "Tomorrow", day + timedelta(days=1))

    results = engine.view("firm-1", CalendarView.DAY, day)

    assert [e.title for e in results] == ["Today"]


def test_week_view_spans_monday_to_sunday() -> None:
    engine = _calendar()
    monday = datetime(2026, 7, 6, 9, 0, tzinfo=UTC)
    wednesday = monday + timedelta(days=2)
    next_monday = monday + timedelta(days=7)
    engine.schedule("firm-1", CalendarEventType.CALL, "This week", wednesday)
    engine.schedule("firm-1", CalendarEventType.CALL, "Next week", next_monday)

    results = engine.view("firm-1", CalendarView.WEEK, monday)

    assert [e.title for e in results] == ["This week"]


def test_month_view_spans_the_calendar_month() -> None:
    engine = _calendar()
    engine.schedule(
        "firm-1", CalendarEventType.CALL, "In July", datetime(2026, 7, 15, tzinfo=UTC)
    )
    engine.schedule(
        "firm-1", CalendarEventType.CALL, "In August", datetime(2026, 8, 1, tzinfo=UTC)
    )

    results = engine.view("firm-1", CalendarView.MONTH, datetime(2026, 7, 1, tzinfo=UTC))

    assert [e.title for e in results] == ["In July"]


def test_agenda_view_returns_future_events_sorted() -> None:
    engine = _calendar()
    now = datetime(2026, 7, 10, tzinfo=UTC)
    engine.schedule("firm-1", CalendarEventType.CALL, "Later", now + timedelta(days=10))
    engine.schedule("firm-1", CalendarEventType.CALL, "Sooner", now + timedelta(days=1))
    engine.schedule("firm-1", CalendarEventType.CALL, "Past", now - timedelta(days=1))

    results = engine.view("firm-1", CalendarView.AGENDA, now)

    assert [e.title for e in results] == ["Sooner", "Later"]


def test_hearing_schedule_creates_calendar_event_and_reminder() -> None:
    calendar_engine = _calendar()
    hearing_engine = HearingEngine(InMemoryHearingStore(), calendar_engine)
    scheduled_at = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)

    hearing = hearing_engine.schedule(
        "firm-1", "case-1", "TJ Paris", "1ere chambre", scheduled_at
    )

    assert hearing.calendar_event_id is not None
    assert hearing.reminder_event_id is not None
    events = calendar_engine.view("firm-1", CalendarView.AGENDA, scheduled_at - timedelta(days=2))
    assert len(events) == 2


def test_hearing_schedule_without_reminder() -> None:
    calendar_engine = _calendar()
    hearing_engine = HearingEngine(InMemoryHearingStore(), calendar_engine)
    scheduled_at = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)

    hearing = hearing_engine.schedule(
        "firm-1", "case-1", "TJ Paris", "1ere chambre", scheduled_at, reminder_before=None
    )

    assert hearing.reminder_event_id is None


def test_hearing_record_decision() -> None:
    calendar_engine = _calendar()
    hearing_engine = HearingEngine(InMemoryHearingStore(), calendar_engine)
    hearing = hearing_engine.schedule(
        "firm-1", "case-1", "TJ Paris", "1ere chambre", datetime(2026, 8, 1, tzinfo=UTC)
    )

    decided = hearing_engine.record_decision(hearing.id, "Renvoi au 15/09")

    assert decided.decision == "Renvoi au 15/09"
    assert decided.decided_at is not None


def test_hearing_add_preparatory_document() -> None:
    calendar_engine = _calendar()
    hearing_engine = HearingEngine(InMemoryHearingStore(), calendar_engine)
    hearing = hearing_engine.schedule(
        "firm-1", "case-1", "TJ Paris", "1ere chambre", datetime(2026, 8, 1, tzinfo=UTC)
    )

    updated = hearing_engine.add_preparatory_document(hearing.id, "doc-1")

    assert "doc-1" in updated.preparatory_document_ids


def test_deadline_engine_has_no_rules_registered_by_default() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())

    created = engine.compute_from_event(
        "firm-1", "case-1", "civil_appeal", "judgment", datetime(2026, 7, 10, tzinfo=UTC)
    )

    assert created == []


def test_deadline_engine_computes_from_a_registered_rule() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())

    class ThirtyDayAppealRule:
        def compute(self, trigger_label: str, trigger_at: datetime) -> list[DeadlineCandidate]:
            return [
                DeadlineCandidate(
                    label=f"Appel — {trigger_label}",
                    due_at=trigger_at + timedelta(days=30),
                    alert_offsets=[timedelta(days=5)],
                )
            ]

    engine.register_rule("civil_appeal", ThirtyDayAppealRule())
    trigger_at = datetime(2026, 7, 10, tzinfo=UTC)

    created = engine.compute_from_event("firm-1", "case-1", "civil_appeal", "judgment", trigger_at)

    assert len(created) == 1
    assert created[0].due_at == trigger_at + timedelta(days=30)
    assert created[0].source_event_label == "judgment"


def test_deadline_manual_create_and_mark_done() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())
    deadline = engine.create(
        "firm-1", "case-1", "Conclusions", datetime(2026, 7, 20, tzinfo=UTC)
    )

    done = engine.mark_done(deadline.id)

    assert done.status is DeadlineStatus.DONE


def test_deadline_mark_missed() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())
    deadline = engine.create(
        "firm-1", "case-1", "Conclusions", datetime(2026, 7, 20, tzinfo=UTC)
    )

    missed = engine.mark_missed(deadline.id)

    assert missed.status is DeadlineStatus.MISSED


def test_deadline_unknown_raises() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())
    with pytest.raises(ValueError, match="Unknown deadline"):
        engine.mark_done("nope")


def test_list_upcoming_only_returns_pending_within_horizon() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())
    now = datetime.now(UTC)
    near = engine.create("firm-1", "case-1", "Near", now + timedelta(days=5))
    far = engine.create("firm-1", "case-1", "Far", now + timedelta(days=60))
    done = engine.create("firm-1", "case-1", "Done", now + timedelta(days=2))
    engine.mark_done(done.id)

    upcoming = engine.list_upcoming("firm-1", timedelta(days=30))

    assert [d.id for d in upcoming] == [near.id]
    assert far.id not in [d.id for d in upcoming]


def test_list_due_alerts_fires_within_offset_window() -> None:
    engine = ConfigurableDeadlineEngine(InMemoryDeadlineStore())
    now = datetime.now(UTC)
    due_at = now + timedelta(days=3)
    engine.create("firm-1", "case-1", "Alerted", due_at, alert_offsets=[timedelta(days=5)])
    engine.create("firm-1", "case-1", "Not yet", due_at, alert_offsets=[timedelta(days=1)])

    due = engine.list_due_alerts("firm-1", now)

    assert [d.label for d in due] == ["Alerted"]
