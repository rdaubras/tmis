from tmis.workflow_automation.event_bus.schemas import WorkflowEvent
from tmis.workflow_automation.trigger_engine.matchers import DEFAULT_MATCHERS
from tmis.workflow_automation.trigger_engine.ports import TriggerMatcherPort
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType


class TriggerEngine:
    """Matches incoming `WorkflowEvent`s against registered `Trigger`s.
    `SCHEDULE` triggers are deliberately not matched here — they are
    fired by `scheduler.SchedulerEngine` polling `next_fire_at`, not by
    an event."""

    def __init__(self, matchers: dict[TriggerType, TriggerMatcherPort] | None = None) -> None:
        self._matchers: dict[TriggerType, TriggerMatcherPort] = matchers or {
            m.trigger_type: m for m in DEFAULT_MATCHERS
        }

    def register(self, matcher: TriggerMatcherPort) -> None:
        self._matchers[matcher.trigger_type] = matcher

    def matches(self, trigger: Trigger, event: WorkflowEvent) -> bool:
        matcher = self._matchers.get(trigger.trigger_type)
        if matcher is None:
            return False
        return matcher.matches(trigger, event)

    def find_matching_triggers(
        self, triggers: list[Trigger], event: WorkflowEvent
    ) -> list[Trigger]:
        return [t for t in triggers if self.matches(t, event)]
