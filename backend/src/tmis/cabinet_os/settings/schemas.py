from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SettingsCategory(str, Enum):
    """The seven categories from the sprint brief."""

    CABINET = "cabinet"
    USERS = "users"
    AI = "ai"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    INTEGRATIONS = "integrations"
    BILLING = "billing"


@dataclass(frozen=True, slots=True)
class SettingEntry:
    """One firm-scoped setting — a plain string value rather than a
    typed schema per key, so a new setting never requires a schema
    change (see docs/39-cabinet-os.md — Settings Engine)."""

    firm_id: str
    category: SettingsCategory
    key: str
    value: str
    updated_at: datetime
