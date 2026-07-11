"""What-if scenarios built from a base case.

A `Scenario` is never a prediction of outcome — it is a structured
"what happens to the strategy if..." exploration, always carrying its
`limitations` (mirrors the "always explained" convention already used
throughout `ai_governance`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


def new_scenario_id() -> str:
    return f"scenario-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    base_case_id: str
    scenario_type: str
    context: str
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    expected_impacts: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
