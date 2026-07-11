import uuid
from dataclasses import dataclass
from enum import StrEnum


class PolicyType(StrEnum):
    """The sprint's "GOVERNANCE" examples: modèles interdits, modèles
    réservés Enterprise, modèles autorisés par pays, modèles autorisés
    pour certains types de données."""

    MODEL_FORBIDDEN = "model_forbidden"
    ENTERPRISE_ONLY = "enterprise_only"
    COUNTRY_RESTRICTED = "country_restricted"
    DATA_TYPE_RESTRICTED = "data_type_restricted"


def new_policy_id() -> str:
    return f"policy-{uuid.uuid4()}"


@dataclass(slots=True)
class Policy:
    id: str
    type: PolicyType
    model_name: str
    reason: str
    allowed_countries: frozenset[str] | None = None
    allowed_data_types: frozenset[str] | None = None
    active: bool = True
