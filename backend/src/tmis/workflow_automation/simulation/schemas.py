from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SimulatedStepOutcome:
    step_order: int
    name: str
    would_run: bool
    skip_reason: str | None = None


@dataclass(frozen=True, slots=True)
class SimulationReport:
    """The predicted shape of a workflow run against fictional data —
    never actually calls `action_engine`, so nothing real is ever
    touched. "Permettre d'exécuter un workflow sur des données
    fictives afin de vérifier son comportement sans impacter les
    dossiers réels" (sprint requirement)."""

    workflow_id: str
    would_complete: bool
    steps: tuple[SimulatedStepOutcome, ...] = field(default_factory=tuple)
    workflow_condition_failure: str | None = None
