from typing import Protocol

from tmis.cabinet_os.contacts.schemas import (
    Contact,
    ContactRelation,
    ContactRelationType,
    ContactRole,
)


class ContactStorePort(Protocol):
    def get(self, contact_id: str) -> Contact | None: ...

    def save(self, contact: Contact) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Contact]: ...


class ContactRelationStorePort(Protocol):
    def save(self, relation: ContactRelation) -> None: ...

    def list_for_contact(self, contact_id: str) -> list[ContactRelation]: ...


class ContactServicePort(Protocol):
    """Port implemented by every interchangeable contact service."""

    def create(
        self,
        firm_id: str,
        role: ContactRole,
        display_name: str,
        *,
        email: str = "",
        phone: str = "",
        organization_client_id: str | None = None,
    ) -> Contact: ...

    def relate(
        self,
        firm_id: str,
        source_contact_id: str,
        target_contact_id: str,
        relation_type: ContactRelationType,
        description: str = "",
    ) -> ContactRelation: ...

    def list_relations(self, contact_id: str) -> list[ContactRelation]: ...
