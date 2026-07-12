from dataclasses import dataclass

from tmis.integration_hub.event_bridge.schemas import EventDirection


@dataclass(slots=True)
class WebhookSubscription:
    """One firm-configured webhook — outbound (TMIS pushes to `url`
    on `event_types`) or inbound (external system pushes to a TMIS
    endpoint, signed with `secret`)."""

    id: str
    connector_id: str
    firm_id: str
    url: str
    direction: EventDirection
    secret: str
    event_types: tuple[str, ...] = ()
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class WebhookDeliveryResult:
    success: bool
    status_code: int | None = None
    detail: str = ""
