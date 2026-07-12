import pytest

from tmis.workflow_automation.event_bus import (
    BusinessEventOccurred,
    CaseUpdated,
    DeadlineApproaching,
    DocumentCreated,
    IntegrationEventReceived,
    ValidationCompleted,
    WorkflowEventBus,
)
from tmis.workflow_automation.trigger_engine import (
    Trigger,
    TriggerEngine,
    TriggerType,
    new_trigger_id,
)


@pytest.mark.asyncio
async def test_event_bus_dispatches_to_subscriber() -> None:
    bus = WorkflowEventBus()
    received = []

    async def handler(event: DocumentCreated) -> None:
        received.append(event)

    bus.subscribe(DocumentCreated, handler)
    event = DocumentCreated(
        firm_id="firm-1", case_id="case-1", document_id="doc-1", document_type="contrat"
    )
    await bus.publish(event)

    assert received == [event]
    assert bus.history == [event]


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_stops_delivery() -> None:
    bus = WorkflowEventBus()
    received = []

    async def handler(event: DocumentCreated) -> None:
        received.append(event)

    bus.subscribe(DocumentCreated, handler)
    bus.unsubscribe(DocumentCreated, handler)
    await bus.publish(
        DocumentCreated(firm_id="firm-1", case_id="case-1", document_id="doc-1", document_type="x")
    )

    assert received == []


def test_trigger_engine_document_created_matches_by_document_type() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.DOCUMENT_CREATED,
        config={"document_type": "contrat"},
    )

    matching = DocumentCreated(
        firm_id="firm-1", case_id="case-1", document_id="d1", document_type="contrat"
    )
    non_matching = DocumentCreated(
        firm_id="firm-1", case_id="case-1", document_id="d2", document_type="facture"
    )

    assert engine.matches(trigger, matching) is True
    assert engine.matches(trigger, non_matching) is False


def test_trigger_engine_deadline_matches_below_threshold() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.DEADLINE,
        config={"days_remaining_at_or_below": "3"},
    )

    close = DeadlineApproaching(
        firm_id="firm-1", case_id="case-1", deadline_label="x", days_remaining=2
    )
    far = DeadlineApproaching(
        firm_id="firm-1", case_id="case-1", deadline_label="x", days_remaining=10
    )

    assert engine.matches(trigger, close) is True
    assert engine.matches(trigger, far) is False


def test_trigger_engine_wrong_event_type_never_matches() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.DOCUMENT_CREATED,
    )

    unrelated = CaseUpdated(firm_id="firm-1", case_id="case-1", field_changed="status")

    assert engine.matches(trigger, unrelated) is False


def test_trigger_engine_business_event_matches_source_and_label() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.BUSINESS_EVENT,
        config={"source": "cabinet_os.hearings", "label": "hearing_created"},
    )

    matching = BusinessEventOccurred(
        firm_id="firm-1", source="cabinet_os.hearings", label="hearing_created"
    )
    non_matching = BusinessEventOccurred(
        firm_id="firm-1", source="cabinet_os.hearings", label="hearing_cancelled"
    )

    assert engine.matches(trigger, matching) is True
    assert engine.matches(trigger, non_matching) is False


def test_trigger_engine_case_updated_matches_field() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.CASE_UPDATED,
        config={"field": "status"},
    )

    matching = CaseUpdated(firm_id="firm-1", case_id="case-1", field_changed="status")
    non_matching = CaseUpdated(firm_id="firm-1", case_id="case-1", field_changed="owner")

    assert engine.matches(trigger, matching) is True
    assert engine.matches(trigger, non_matching) is False


def test_trigger_engine_validation_matches_only_when_approved() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.VALIDATION,
        config={"target_type": "draft"},
    )

    approved = ValidationCompleted(
        firm_id="firm-1", target_type="draft", target_id="d1", approved=True
    )
    rejected = ValidationCompleted(
        firm_id="firm-1", target_type="draft", target_id="d1", approved=False
    )
    wrong_target = ValidationCompleted(
        firm_id="firm-1", target_type="strategy", target_id="s1", approved=True
    )

    assert engine.matches(trigger, approved) is True
    assert engine.matches(trigger, rejected) is False
    assert engine.matches(trigger, wrong_target) is False


def test_trigger_engine_integration_event_matches_by_name() -> None:
    engine = TriggerEngine()
    trigger = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.INTEGRATION_EVENT,
        config={"integration_name": "calendar"},
    )

    matching = IntegrationEventReceived(
        firm_id="firm-1", integration_name="calendar", label="synced"
    )
    non_matching = IntegrationEventReceived(
        firm_id="firm-1", integration_name="ged", label="synced"
    )

    assert engine.matches(trigger, matching) is True
    assert engine.matches(trigger, non_matching) is False


def test_trigger_engine_unregistered_trigger_type_never_matches() -> None:
    engine = TriggerEngine(matchers={})
    trigger = Trigger(id=new_trigger_id(), workflow_id="wf-1", trigger_type=TriggerType.SCHEDULE)

    event = CaseUpdated(firm_id="firm-1", case_id="case-1", field_changed="status")

    assert engine.matches(trigger, event) is False


def test_trigger_engine_find_matching_triggers_filters_list() -> None:
    engine = TriggerEngine()
    t1 = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-1",
        trigger_type=TriggerType.DOCUMENT_CREATED,
        config={"document_type": "contrat"},
    )
    t2 = Trigger(
        id=new_trigger_id(),
        workflow_id="wf-2",
        trigger_type=TriggerType.DOCUMENT_CREATED,
        config={"document_type": "facture"},
    )

    event = DocumentCreated(
        firm_id="firm-1", case_id="case-1", document_id="d1", document_type="contrat"
    )

    assert engine.find_matching_triggers([t1, t2], event) == [t1]
