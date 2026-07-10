from dataclasses import dataclass, field
from enum import Enum


class ActorType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    ADMINISTRATION = "administration"
    JURISDICTION = "jurisdiction"
    EXPERT = "expert"
    WITNESS = "witness"


class CaseActorRole(str, Enum):
    """An actor's role within one particular case — distinct from
    `ActorType`, which is the actor's intrinsic legal nature. The same
    person could be a witness in one case and a client in another."""

    CLIENT = "client"
    OPPOSING_PARTY = "opposing_party"
    LAWYER = "lawyer"
    JURISDICTION = "jurisdiction"
    OTHER = "other"


@dataclass
class Actor:
    """A person, company or institution referenced in a case's documents.

    Mutable on purpose: `ActorMerger` updates `aliases` and
    `source_document_ids` in place as new documents are processed.
    """

    id: str
    type: ActorType
    name: str
    aliases: set[str] = field(default_factory=set)
    source_document_ids: set[str] = field(default_factory=set)
