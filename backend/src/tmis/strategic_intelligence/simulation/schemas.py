import uuid
from dataclasses import dataclass, field


def new_simulation_id() -> str:
    return f"sim-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    id: str
    base_case_id: str
    variable_changes: dict[str, str] = field(default_factory=dict)
    hypotheticals: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Purely structural: lists which strategies *reference* elements
    mentioned in the hypothetical changes. Never a judicial prediction
    — "aucune prédiction judiciaire ne doit être fournie dans ce
    sprint" (sprint requirement) — hence no probability, score or
    outcome field anywhere in this schema."""

    scenario_id: str
    affected_strategy_ids: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)
