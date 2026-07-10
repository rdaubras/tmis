from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ClientType(str, Enum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"


class ClientStatus(str, Enum):
    PROSPECT = "prospect"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Address:
    street: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = "FR"


@dataclass(frozen=True, slots=True)
class ClientNote:
    """A note attached to a client — appended to `Client.notes`, never
    overwritten (same append-only discipline as
    `tmis.collaboration.members.schemas.MemberHistoryEntry`)."""

    id: str
    author_id: str
    text: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ClientHistoryEntry:
    timestamp: datetime
    from_status: ClientStatus | None
    to_status: ClientStatus
    actor_id: str | None


@dataclass(slots=True)
class Client:
    """A client of the firm — physical or legal person (see
    docs/40-guide-crm.md). Only *ids* to other bounded contexts are
    kept here (`case_ids`, `document_ids`, `contact_ids`,
    `invoice_ids`) — the same discipline as
    `tmis.collaboration.workspace.Workspace`."""

    id: str
    firm_id: str
    client_type: ClientType
    display_name: str
    email: str = ""
    phone: str = ""
    address: Address = field(default_factory=Address)
    # Individual-only fields (empty for organizations).
    first_name: str = ""
    last_name: str = ""
    date_of_birth: datetime | None = None
    # Organization-only fields (empty for individuals).
    legal_form: str = ""
    registration_number: str = ""
    vat_number: str = ""
    status: ClientStatus = ClientStatus.PROSPECT
    case_ids: set[str] = field(default_factory=set)
    document_ids: set[str] = field(default_factory=set)
    contact_ids: set[str] = field(default_factory=set)
    invoice_ids: set[str] = field(default_factory=set)
    notes: list[ClientNote] = field(default_factory=list)
    history: list[ClientHistoryEntry] = field(default_factory=list)
    created_at: datetime | None = None
