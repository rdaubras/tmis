from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContactRole(str, Enum):
    """The six contact categories from the sprint brief."""

    EXECUTIVE = "executive"  # dirigeant
    REPRESENTATIVE = "representative"  # représentant
    EXPERT = "expert"
    WITNESS = "witness"  # témoin
    ADMINISTRATION = "administration"
    PARTNER = "partner"  # partenaire


class ContactRelationType(str, Enum):
    """Generic relation vocabulary between two contacts — deliberately
    small and open-ended rather than one enum value per possible legal
    relationship."""

    WORKS_FOR = "works_for"
    REPRESENTS = "represents"
    EMPLOYS = "employs"
    RELATED_TO = "related_to"


@dataclass(slots=True)
class Contact:
    """A person or entity relevant to a firm's activity but not itself
    a client — an executive, representative, expert, witness,
    administration or partner (see docs/40-guide-crm.md).
    `organization_client_id` optionally links the contact to the
    `Client` (organization) they belong to, by id only."""

    id: str
    firm_id: str
    role: ContactRole
    display_name: str
    email: str = ""
    phone: str = ""
    organization_client_id: str | None = None
    notes: str = ""
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ContactRelation:
    """A directed relation between two contacts (see
    docs/40-guide-crm.md — Contact Engine)."""

    id: str
    firm_id: str
    source_contact_id: str
    target_contact_id: str
    relation_type: ContactRelationType
    description: str = ""
