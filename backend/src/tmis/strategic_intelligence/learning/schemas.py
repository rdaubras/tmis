import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class StrategyOutcome(StrEnum):
    CHOSEN = "chosen"
    VALIDATED = "validated"
    REJECTED = "rejected"
    MODIFIED = "modified"


def new_learning_record_id() -> str:
    return f"learn-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class LearningRecord:
    id: str
    firm_id: str
    case_id: str
    strategy_id: str
    strategy_type: str
    outcome: StrategyOutcome
    actor: str
    comment: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
