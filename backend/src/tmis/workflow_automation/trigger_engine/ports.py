from typing import Protocol

from tmis.workflow_automation.event_bus.schemas import WorkflowEvent
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType


class TriggerMatcherPort(Protocol):
    """One pluggable trigger-type matcher. `TriggerEngine` is closed
    over this narrow contract so a new trigger type (e.g. a future
    integration-specific trigger) can be registered without touching
    the engine — same extensibility pattern as
    `ai_governance.bias_detection.BiasDetectorPort`."""

    trigger_type: TriggerType

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool: ...
