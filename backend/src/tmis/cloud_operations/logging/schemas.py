from dataclasses import dataclass
from enum import StrEnum


class LogRetentionCategory(StrEnum):
    """The log families the sprint asks for a "conservation
    configurable" (configurable retention) on — distinct retention
    windows because their compliance/operational value differs
    (audit logs must outlive application debug logs)."""

    APPLICATION = "application"
    SECURITY = "security"
    AUDIT = "audit"
    AI_INTERACTION = "ai_interaction"


@dataclass(frozen=True, slots=True)
class LogRetentionPolicy:
    category: LogRetentionCategory
    retention_days: int
