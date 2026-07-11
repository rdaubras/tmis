import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.platform_sdk.plugin_system.schemas import PublishingStatus

ALLOWED_TRANSITIONS: dict[PublishingStatus, frozenset[PublishingStatus]] = {
    PublishingStatus.DEVELOPMENT: frozenset({PublishingStatus.VALIDATED}),
    PublishingStatus.VALIDATED: frozenset(
        {PublishingStatus.SIGNED, PublishingStatus.DEVELOPMENT}
    ),
    PublishingStatus.SIGNED: frozenset({PublishingStatus.PUBLISHED, PublishingStatus.DEVELOPMENT}),
    PublishingStatus.PUBLISHED: frozenset({PublishingStatus.RETIRED}),
    PublishingStatus.RETIRED: frozenset(),
}


class InvalidPublishingTransitionError(ValueError):
    def __init__(self, from_status: PublishingStatus, to_status: PublishingStatus) -> None:
        super().__init__(f"Cannot transition from {from_status.value} to {to_status.value}")


class ValidationFailedError(ValueError):
    pass


def new_publishing_event_id() -> str:
    return f"pubevt-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class PublishingEvent:
    id: str
    plugin_id: str
    from_status: PublishingStatus
    to_status: PublishingStatus
    actor: str
    reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
