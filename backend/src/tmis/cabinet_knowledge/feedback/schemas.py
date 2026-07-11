import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class FeedbackAction(StrEnum):
    ACCEPT = "accept"
    MODIFY = "modify"
    REJECT = "reject"
    ANNOTATE = "annotate"
    EXPLAIN = "explain"


def new_feedback_id() -> str:
    return f"fb-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class Feedback:
    id: str
    firm_id: str
    knowledge_object_id: str
    action: FeedbackAction
    author: str
    comment: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
