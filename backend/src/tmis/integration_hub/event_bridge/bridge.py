from tmis.integration_hub.event_bridge.bus import IntegrationEventBus
from tmis.integration_hub.event_bridge.schemas import ExternalRecordChanged
from tmis.workflow_automation.event_bus.bus import WorkflowEventBus
from tmis.workflow_automation.event_bus.schemas import IntegrationEventReceived


class EventBridge:
    """Bridges `integration_hub.event_bridge.IntegrationEventBus`
    (external-system events) to
    `workflow_automation.event_bus.WorkflowEventBus` —
    "fait le pont entre les événements internes de TMIS et les
    événements des systèmes externes" (sprint requirement). A direct,
    explicit dependency rather than a decoupled Protocol: bridging
    these two named systems together is this class's entire purpose,
    and `workflow_automation.event_bus.IntegrationEventReceived`
    already exists precisely to receive what this bridge forwards."""

    def __init__(
        self, integration_bus: IntegrationEventBus, workflow_bus: WorkflowEventBus | None = None
    ) -> None:
        self._workflow_bus = workflow_bus
        integration_bus.subscribe(ExternalRecordChanged, self._forward_to_workflow)

    async def _forward_to_workflow(self, event: ExternalRecordChanged) -> None:
        if self._workflow_bus is None:
            return
        await self._workflow_bus.publish(
            IntegrationEventReceived(
                firm_id=event.firm_id,
                integration_name=event.connector_id,
                label=event.entity_type,
                payload=event.payload,
            )
        )
