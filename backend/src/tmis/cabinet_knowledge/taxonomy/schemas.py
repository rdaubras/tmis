import uuid
from dataclasses import dataclass
from enum import StrEnum


class LegalDomain(StrEnum):
    """A cabinet_knowledge-local copy of the legal-domain vocabulary
    (see also `tmis.ai_team.capabilities.schemas.LegalDomain`) — kept
    independent rather than imported, since no bounded context in TMIS
    shares a common vocabulary package (each Sprint 2-11 module has
    always defined its own domain enums; see docs/59-architecture-
    cabinet-knowledge-engine.md for the rationale). The values are
    kept in sync deliberately for consistency across the product."""

    GENERAL = "general"
    CIVIL = "civil"
    COMMERCIAL = "commercial"
    SOCIAL = "social"
    FISCAL = "fiscal"
    DATA_PROTECTION = "data_protection"
    PENAL = "penal"


def new_taxonomy_node_id() -> str:
    return f"taxo-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class TaxonomyNode:
    id: str
    label: str
    domain: LegalDomain
    parent_id: str | None = None
