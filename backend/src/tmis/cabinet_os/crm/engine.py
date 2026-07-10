from tmis.cabinet_os.clients.ports import ClientStorePort
from tmis.cabinet_os.clients.schemas import Client
from tmis.cabinet_os.contacts.ports import ContactStorePort
from tmis.cabinet_os.crm.schemas import ClientProfile


class CRMEngine:
    """Implements `CRMEnginePort`: the composition root of the CRM (see
    docs/40-guide-crm.md). It never re-implements client or contact
    persistence — it resolves ids into a read-model `ClientProfile`."""

    def __init__(self, client_store: ClientStorePort, contact_store: ContactStorePort) -> None:
        self._clients = client_store
        self._contacts = contact_store

    def get_profile(self, client_id: str) -> ClientProfile:
        client = self._clients.get(client_id)
        if client is None:
            raise ValueError(f"Unknown client {client_id!r}")
        contacts = [
            contact
            for contact_id in client.contact_ids
            if (contact := self._contacts.get(contact_id)) is not None
        ]
        return ClientProfile(
            client=client,
            contacts=contacts,
            case_ids=list(client.case_ids),
            document_ids=list(client.document_ids),
            invoice_ids=list(client.invoice_ids),
        )

    def search(self, firm_id: str, query: str) -> list[Client]:
        needle = query.strip().lower()
        if not needle:
            return self._clients.list_for_firm(firm_id)
        return [
            c
            for c in self._clients.list_for_firm(firm_id)
            if needle in c.display_name.lower() or needle in c.email.lower()
        ]
