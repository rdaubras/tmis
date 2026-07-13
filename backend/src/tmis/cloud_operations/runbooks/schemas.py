from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RunbookStep:
    order: int
    instruction: str


@dataclass(frozen=True, slots=True)
class Runbook:
    """One operational procedure — the sprint's examples ("fournisseur
    IA indisponible, base de données lente, surcharge, échec de
    synchronisation, incident Marketplace") are seeded by `library.
    DEFAULT_RUNBOOKS` below."""

    slug: str
    title: str
    trigger: str
    steps: list[RunbookStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
