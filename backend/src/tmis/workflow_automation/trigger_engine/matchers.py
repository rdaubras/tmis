from tmis.workflow_automation.event_bus.schemas import (
    BusinessEventOccurred,
    CaseUpdated,
    DeadlineApproaching,
    DocumentCreated,
    IntegrationEventReceived,
    ValidationCompleted,
    WorkflowEvent,
)
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType


class BusinessEventMatcher:
    trigger_type = TriggerType.BUSINESS_EVENT

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, BusinessEventOccurred):
            return False
        return event.source == trigger.config.get("source") and event.label == trigger.config.get(
            "label"
        )


class DeadlineMatcher:
    trigger_type = TriggerType.DEADLINE

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, DeadlineApproaching):
            return False
        threshold = trigger.config.get("days_remaining_at_or_below")
        if threshold is None:
            return True
        return event.days_remaining <= int(threshold)


class DocumentCreatedMatcher:
    trigger_type = TriggerType.DOCUMENT_CREATED

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, DocumentCreated):
            return False
        document_type = trigger.config.get("document_type")
        return document_type is None or event.document_type == document_type


class CaseUpdatedMatcher:
    trigger_type = TriggerType.CASE_UPDATED

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, CaseUpdated):
            return False
        field_changed = trigger.config.get("field")
        return field_changed is None or event.field_changed == field_changed


class ValidationMatcher:
    trigger_type = TriggerType.VALIDATION

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, ValidationCompleted):
            return False
        target_type = trigger.config.get("target_type")
        return event.approved and (target_type is None or event.target_type == target_type)


class IntegrationEventMatcher:
    trigger_type = TriggerType.INTEGRATION_EVENT

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        if not isinstance(event, IntegrationEventReceived):
            return False
        integration_name = trigger.config.get("integration_name")
        return integration_name is None or event.integration_name == integration_name


DEFAULT_MATCHERS = (
    BusinessEventMatcher(),
    DeadlineMatcher(),
    DocumentCreatedMatcher(),
    CaseUpdatedMatcher(),
    ValidationMatcher(),
    IntegrationEventMatcher(),
)
