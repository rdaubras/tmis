from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class ManagedSecret:
    key: str
    firm_id: str
    encrypted_value: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    rotated_at: datetime | None = None
