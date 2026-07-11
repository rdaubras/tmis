import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TraceEntryKind(StrEnum):
    """The sprint's explicit traceability chain: utilisateur, dossier,
    version des modèles, prompts utilisés, réponses intermédiaires,
    validations humaines, décisions finales."""

    USER = "user"
    CASE = "case"
    MODEL_VERSION = "model_version"
    PROMPT = "prompt"
    INTERMEDIATE_RESPONSE = "intermediate_response"
    HUMAN_VALIDATION = "human_validation"
    FINAL_DECISION = "final_decision"


def new_trace_entry_id() -> str:
    return f"trace-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class TraceEntry:
    """One traced element — always carries `reference`, the unique
    identifier of the element being traced (user id, case id, model
    name+version, prompt id, response id, validation id, decision
    id), per the sprint's "chaque élément doit être relié à un
    identifiant unique"."""

    id: str
    firm_id: str
    production_id: str
    kind: TraceEntryKind
    reference: str
    detail: str
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
