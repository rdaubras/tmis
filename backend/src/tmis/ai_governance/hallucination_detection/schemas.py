import uuid
from dataclasses import dataclass


def new_hallucination_alert_id() -> str:
    return f"halluc-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class HallucinationAlert:
    """The sprint's explicit constraint: "ne jamais supprimer
    automatiquement un contenu" — this engine only ever produces
    alerts with a `recommendation`, never mutates or removes text."""

    id: str
    excerpt: str
    reason: str
    recommendation: str
