from dataclasses import dataclass
from enum import StrEnum


class Likelihood(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ProbabilityAssessment:
    """A qualitative likelihood on a *sub-element* of a strategy (e.g.
    evidence admissibility, argument acceptance) — deliberately never a
    case-outcome win-probability. This is a direct compliance measure
    for the sprint's "aucune prédiction de résultat d'un procès ne doit
    être présentée comme certaine" constraint: there is no field here
    that could be read as a trial prediction."""

    element_description: str
    likelihood: Likelihood
    rationale: str
