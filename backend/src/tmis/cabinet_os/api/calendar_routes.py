from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from tmis.cabinet_os.api.schemas import (
    CalendarEventResponse,
    CreateDeadlineRequest,
    DeadlineResponse,
    HearingResponse,
    RecordHearingDecisionRequest,
    ScheduleEventRequest,
    ScheduleHearingRequest,
)
from tmis.cabinet_os.bootstrap import get_calendar_engine, get_deadline_engine, get_hearing_engine
from tmis.cabinet_os.calendar.engine import ConfigurableCalendarEngine
from tmis.cabinet_os.calendar.schemas import CalendarEvent, CalendarEventType, CalendarView
from tmis.cabinet_os.deadlines.engine import ConfigurableDeadlineEngine
from tmis.cabinet_os.deadlines.schemas import Deadline
from tmis.cabinet_os.hearings.engine import HearingEngine
from tmis.cabinet_os.hearings.schemas import Hearing

router = APIRouter(prefix="/cabinet-os", tags=["cabinet-os-calendar"])


def _to_event_response(event: CalendarEvent) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=event.id,
        firm_id=event.firm_id,
        event_type=event.event_type.value,
        title=event.title,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        location=event.location,
    )


def _to_hearing_response(hearing: Hearing) -> HearingResponse:
    return HearingResponse(
        id=hearing.id,
        firm_id=hearing.firm_id,
        case_id=hearing.case_id,
        jurisdiction=hearing.jurisdiction,
        chamber=hearing.chamber,
        scheduled_at=hearing.scheduled_at,
        room=hearing.room,
        decision=hearing.decision,
        calendar_event_id=hearing.calendar_event_id,
        reminder_event_id=hearing.reminder_event_id,
    )


def _to_deadline_response(deadline: Deadline) -> DeadlineResponse:
    return DeadlineResponse(
        id=deadline.id,
        firm_id=deadline.firm_id,
        case_id=deadline.case_id,
        label=deadline.label,
        due_at=deadline.due_at,
        status=deadline.status.value,
    )


@router.post("/calendar/events", response_model=CalendarEventResponse)
def schedule_event(
    payload: ScheduleEventRequest,
    engine: ConfigurableCalendarEngine = Depends(get_calendar_engine),
) -> CalendarEventResponse:
    try:
        event_type = CalendarEventType(payload.event_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown event type: {payload.event_type!r}"
        ) from exc
    event = engine.schedule(
        payload.firm_id,
        event_type,
        payload.title,
        payload.starts_at,
        ends_at=payload.ends_at,
        case_id=payload.case_id,
        location=payload.location,
    )
    return _to_event_response(event)


@router.get("/calendar/view", response_model=list[CalendarEventResponse])
def view_calendar(
    firm_id: str,
    view: str,
    reference_date: str,
    engine: ConfigurableCalendarEngine = Depends(get_calendar_engine),
) -> list[CalendarEventResponse]:
    try:
        parsed_view = CalendarView(view)
        parsed_date = datetime.fromisoformat(reference_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    events = engine.view(firm_id, parsed_view, parsed_date)
    return [_to_event_response(e) for e in events]


@router.post("/hearings", response_model=HearingResponse)
def schedule_hearing(
    payload: ScheduleHearingRequest,
    engine: HearingEngine = Depends(get_hearing_engine),
) -> HearingResponse:
    hearing = engine.schedule(
        payload.firm_id,
        payload.case_id,
        payload.jurisdiction,
        payload.chamber,
        payload.scheduled_at,
        room=payload.room,
    )
    return _to_hearing_response(hearing)


@router.post("/hearings/{hearing_id}/decision", response_model=HearingResponse)
def record_hearing_decision(
    hearing_id: str,
    payload: RecordHearingDecisionRequest,
    engine: HearingEngine = Depends(get_hearing_engine),
) -> HearingResponse:
    try:
        hearing = engine.record_decision(hearing_id, payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_hearing_response(hearing)


@router.get("/hearings", response_model=list[HearingResponse])
def list_hearings_for_case(
    case_id: str, engine: HearingEngine = Depends(get_hearing_engine)
) -> list[HearingResponse]:
    return [_to_hearing_response(h) for h in engine.list_for_case(case_id)]


@router.post("/deadlines", response_model=DeadlineResponse)
def create_deadline(
    payload: CreateDeadlineRequest,
    engine: ConfigurableDeadlineEngine = Depends(get_deadline_engine),
) -> DeadlineResponse:
    deadline = engine.create(payload.firm_id, payload.case_id, payload.label, payload.due_at)
    return _to_deadline_response(deadline)


@router.get("/deadlines", response_model=list[DeadlineResponse])
def list_upcoming_deadlines(
    firm_id: str,
    within_days: int = 30,
    engine: ConfigurableDeadlineEngine = Depends(get_deadline_engine),
) -> list[DeadlineResponse]:
    deadlines = engine.list_upcoming(firm_id, timedelta(days=within_days))
    return [_to_deadline_response(d) for d in deadlines]


@router.post("/deadlines/{deadline_id}/done", response_model=DeadlineResponse)
def mark_deadline_done(
    deadline_id: str, engine: ConfigurableDeadlineEngine = Depends(get_deadline_engine)
) -> DeadlineResponse:
    try:
        deadline = engine.mark_done(deadline_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_deadline_response(deadline)


@router.post("/deadlines/{deadline_id}/missed", response_model=DeadlineResponse)
def mark_deadline_missed(
    deadline_id: str, engine: ConfigurableDeadlineEngine = Depends(get_deadline_engine)
) -> DeadlineResponse:
    try:
        deadline = engine.mark_missed(deadline_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_deadline_response(deadline)
