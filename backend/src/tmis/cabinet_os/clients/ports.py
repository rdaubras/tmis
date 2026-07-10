from typing import Protocol

from tmis.cabinet_os.clients.schemas import Address, Client, ClientStatus, ClientType


class ClientStorePort(Protocol):
    """Port implemented by every interchangeable client store."""

    def get(self, client_id: str) -> Client | None: ...

    def save(self, client: Client) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Client]: ...


class ClientServicePort(Protocol):
    """Port implemented by every interchangeable client service."""

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
    ) -> Client: ...

    def change_status(
        self, client_id: str, target: ClientStatus, actor_id: str | None = None
    ) -> Client: ...

    def add_note(self, client_id: str, author_id: str, text: str) -> Client: ...

    def link_case(self, client_id: str, case_id: str) -> Client: ...

    def link_document(self, client_id: str, document_id: str) -> Client: ...

    def link_contact(self, client_id: str, contact_id: str) -> Client: ...
