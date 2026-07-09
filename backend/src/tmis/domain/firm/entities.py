import uuid
from dataclasses import dataclass
from enum import Enum


class SubscriptionPlan(str, Enum):
    SOLO = "solo"
    CABINET = "cabinet"
    ENTERPRISE = "enterprise"


@dataclass
class Firm:
    """Aggregate root of the `firm` bounded context (tenant)."""

    id: uuid.UUID
    name: str
    plan: SubscriptionPlan
    is_active: bool = True
