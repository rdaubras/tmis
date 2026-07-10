from dataclasses import dataclass, field

from tmis.cabinet_os.clients.schemas import Client
from tmis.cabinet_os.contacts.schemas import Contact


@dataclass(frozen=True, slots=True)
class ClientProfile:
    """The 360-degree view of a client (see docs/40-guide-crm.md): the
    `Client` aggregate plus its resolved contacts, with dossiers,
    documents and invoices kept as **ids only** — CRM composes what
    other engines (`case_intelligence`, cabinet_os `documents`/
    `billing`) already own, it never embeds their aggregates, the same
    discipline as `tmis.collaboration.workspace.Workspace`."""

    client: Client
    contacts: list[Contact] = field(default_factory=list)
    case_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    invoice_ids: list[str] = field(default_factory=list)
