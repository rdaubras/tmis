import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_explainability_report_id() -> str:
    return f"expl-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class IgnoredElement:
    """Something the production considered but did not use — always
    justified, per the sprint's "éléments ignorés et justification"."""

    description: str
    justification: str


@dataclass(frozen=True, slots=True)
class ExplainabilityReport:
    """Answers, for one AI production, the sprint's Vision questions:
    pourquoi cette réponse, quelles étapes, quels agents, quels
    modèles, quelles références, quels documents, quels éléments
    ignorés. Written to be readable by a lawyer, not a developer —
    every field is a sentence or a list of sentences, never a raw
    identifier alone."""

    id: str
    firm_id: str
    production_id: str
    summary: str
    steps_followed: tuple[str, ...]
    agents_involved: tuple[str, ...]
    models_used: tuple[str, ...]
    legal_references: tuple[str, ...]
    documents_consulted: tuple[str, ...]
    ignored_elements: tuple[IgnoredElement, ...] = field(default_factory=tuple)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
