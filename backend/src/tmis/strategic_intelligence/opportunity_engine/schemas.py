import uuid
from dataclasses import dataclass


def new_opportunity_id() -> str:
    return f"opp-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class OpportunityFinding:
    """A single spotted opportunity — always carries `justification`,
    never a bare flag, matching the "always explained" convention of
    `ai_governance.bias_detection.BiasFinding`. `category` is a
    free-form string so a new finding family can be added without
    editing this schema."""

    id: str
    category: str
    description: str
    justification: str
