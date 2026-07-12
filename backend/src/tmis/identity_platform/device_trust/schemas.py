import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class DeviceTrustLevel(StrEnum):
    UNKNOWN = "unknown"
    TRUSTED = "trusted"
    REVOKED = "revoked"


def new_device_id() -> str:
    return f"device-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Device:
    id: str
    firm_id: str
    user_id: str
    label: str
    trust_level: DeviceTrustLevel = DeviceTrustLevel.UNKNOWN
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
