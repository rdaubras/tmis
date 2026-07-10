import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.calendar.ports import CalendarEnginePort
from tmis.cabinet_os.calendar.schemas import CalendarEventType
from tmis.cabinet_os.hearings.ports import HearingStorePort
from tmis.cabinet_os.hearings.schemas import Hearing


class HearingEngine:
    """Implements `HearingEnginePort` (see docs/39-cabinet-os.md —
    Hearing Engine). Scheduling a hearing always creates a matching
    `CalendarEvent` (and, by default, a reminder one day before) via
    the injected `CalendarEnginePort` — the Hearing Engine never
    maintains its own notion of "when", it composes the Calendar
    Engine instead."""

    def __init__(self, store: HearingStorePort, calendar_engine: CalendarEnginePort) -> None:
        self._store = store
        self._calendar = calendar_engine

    def schedule(
        self,
        firm_id: str,
        case_id: str,
        jurisdiction: str,
        chamber: str,
        scheduled_at: datetime,
        *,
        room: str = "",
        participant_ids: set[str] | None = None,
        reminder_before: timedelta | None = timedelta(days=1),
    ) -> Hearing:
        hearing_id = str(uuid.uuid4())
        calendar_event = self._calendar.schedule(
            firm_id,
            CalendarEventType.HEARING,
            f"Audience — {jurisdiction} ({chamber})",
            scheduled_at,
            case_id=case_id,
            participant_ids=participant_ids,
            location=room,
            related_id=hearing_id,
        )
        reminder_event_id = None
        if reminder_before is not None:
            reminder_event = self._calendar.schedule(
                firm_id,
                CalendarEventType.REMINDER,
                f"Rappel — audience {jurisdiction} ({chamber})",
                scheduled_at - reminder_before,
                case_id=case_id,
                related_id=hearing_id,
            )
            reminder_event_id = reminder_event.id
        hearing = Hearing(
            id=hearing_id,
            firm_id=firm_id,
            case_id=case_id,
            jurisdiction=jurisdiction,
            chamber=chamber,
            scheduled_at=scheduled_at,
            room=room,
            participant_ids=set(participant_ids or set()),
            calendar_event_id=calendar_event.id,
            reminder_event_id=reminder_event_id,
            created_at=datetime.now(UTC),
        )
        self._store.save(hearing)
        return hearing

    def record_decision(self, hearing_id: str, decision: str) -> Hearing:
        hearing = self._require(hearing_id)
        hearing.decision = decision
        hearing.decided_at = datetime.now(UTC)
        self._store.save(hearing)
        return hearing

    def add_preparatory_document(self, hearing_id: str, document_id: str) -> Hearing:
        hearing = self._require(hearing_id)
        hearing.preparatory_document_ids.add(document_id)
        self._store.save(hearing)
        return hearing

    def list_for_case(self, case_id: str) -> list[Hearing]:
        return self._store.list_for_case(case_id)

    def _require(self, hearing_id: str) -> Hearing:
        hearing = self._store.get(hearing_id)
        if hearing is None:
            raise ValueError(f"Unknown hearing {hearing_id!r}")
        return hearing
