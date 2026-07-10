import uuid
from datetime import UTC, datetime

from tmis.cabinet_os.clients.ports import ClientStorePort
from tmis.cabinet_os.clients.schemas import (
    Address,
    Client,
    ClientHistoryEntry,
    ClientNote,
    ClientStatus,
    ClientType,
)
from tmis.cabinet_os.clients.store import InMemoryClientStore

_ALLOWED_TRANSITIONS: dict[ClientStatus, set[ClientStatus]] = {
    ClientStatus.PROSPECT: {ClientStatus.ACTIVE, ClientStatus.ARCHIVED},
    ClientStatus.ACTIVE: {ClientStatus.ARCHIVED},
    ClientStatus.ARCHIVED: {ClientStatus.ACTIVE},
}


class ClientService:
    """Implements `ClientServicePort`: creates and mutates `Client`s,
    covering both physical and legal persons (see docs/40-guide-crm.md).
    Status transitions are checked against `_ALLOWED_TRANSITIONS` and
    appended to `Client.history`, never overwriting a previous entry —
    same discipline as `tmis.collaboration.members.MemberService`."""

    def __init__(self, store: ClientStorePort | None = None) -> None:
        self._store: ClientStorePort = store or InMemoryClientStore()

    def create(
        self,
        firm_id: str,
        client_type: ClientType,
        display_name: str,
        *,
        email: str = "",
        phone: str = "",
        address: Address | None = None,
        first_name: str = "",
        last_name: str = "",
        legal_form: str = "",
        registration_number: str = "",
        vat_number: str = "",
    ) -> Client:
        now = datetime.now(UTC)
        client = Client(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            client_type=client_type,
            display_name=display_name,
            email=email,
            phone=phone,
            address=address or Address(),
            first_name=first_name,
            last_name=last_name,
            legal_form=legal_form,
            registration_number=registration_number,
            vat_number=vat_number,
            created_at=now,
            history=[
                ClientHistoryEntry(
                    timestamp=now,
                    from_status=None,
                    to_status=ClientStatus.PROSPECT,
                    actor_id=None,
                )
            ],
        )
        self._store.save(client)
        return client

    def change_status(
        self, client_id: str, target: ClientStatus, actor_id: str | None = None
    ) -> Client:
        client = self._require(client_id)
        allowed = _ALLOWED_TRANSITIONS.get(client.status, set())
        if target not in allowed:
            raise ValueError(f"Cannot transition client from {client.status} to {target}")
        client.history.append(
            ClientHistoryEntry(
                timestamp=datetime.now(UTC),
                from_status=client.status,
                to_status=target,
                actor_id=actor_id,
            )
        )
        client.status = target
        self._store.save(client)
        return client

    def add_note(self, client_id: str, author_id: str, text: str) -> Client:
        client = self._require(client_id)
        client.notes.append(
            ClientNote(
                id=str(uuid.uuid4()), author_id=author_id, text=text, created_at=datetime.now(UTC)
            )
        )
        self._store.save(client)
        return client

    def link_case(self, client_id: str, case_id: str) -> Client:
        client = self._require(client_id)
        client.case_ids.add(case_id)
        self._store.save(client)
        return client

    def link_document(self, client_id: str, document_id: str) -> Client:
        client = self._require(client_id)
        client.document_ids.add(document_id)
        self._store.save(client)
        return client

    def link_contact(self, client_id: str, contact_id: str) -> Client:
        client = self._require(client_id)
        client.contact_ids.add(contact_id)
        self._store.save(client)
        return client

    def _require(self, client_id: str) -> Client:
        client = self._store.get(client_id)
        if client is None:
            raise ValueError(f"Unknown client {client_id!r}")
        return client
