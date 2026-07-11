import uuid
from dataclasses import dataclass


def new_ethics_finding_id() -> str:
    return f"ethics-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class EthicsFinding:
    """Advisory only — the Ethics Engine never blocks a production
    automatically, it only flags a concern for human review."""

    id: str
    category: str
    excerpt: str
    description: str
    explanation: str
