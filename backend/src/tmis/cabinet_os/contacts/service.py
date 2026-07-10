import uuid
from datetime import UTC, datetime

from tmis.cabinet_os.contacts.ports import ContactRelationStorePort, ContactStorePort
from tmis.cabinet_os.contacts.schemas import (
    Contact,
    ContactRelation,
    ContactRelationType,
    ContactRole,
)
from tmis.cabinet_os.contacts.store import InMemoryContactRelationStore, InMemoryContactStore


class ContactService:
    """Implements `ContactServicePort` (see docs/40-guide-crm.md —
    Contact Engine)."""

    def __init__(
        self,
        store: ContactStorePort | None = None,
        relation_store: ContactRelationStorePort | None = None,
    ) -> None:
        self._store: ContactStorePort = store or InMemoryContactStore()
        self._relations: ContactRelationStorePort = relation_store or InMemoryContactRelationStore()

    def create(
        self,
        firm_id: str,
        role: ContactRole,
        display_name: str,
        *,
        email: str = "",
        phone: str = "",
        organization_client_id: str | None = None,
    ) -> Contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            role=role,
            display_name=display_name,
            email=email,
            phone=phone,
            organization_client_id=organization_client_id,
            created_at=datetime.now(UTC),
        )
        self._store.save(contact)
        return contact

    def relate(
        self,
        firm_id: str,
        source_contact_id: str,
        target_contact_id: str,
        relation_type: ContactRelationType,
        description: str = "",
    ) -> ContactRelation:
        relation = ContactRelation(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            source_contact_id=source_contact_id,
            target_contact_id=target_contact_id,
            relation_type=relation_type,
            description=description,
        )
        self._relations.save(relation)
        return relation

    def list_relations(self, contact_id: str) -> list[ContactRelation]:
        return self._relations.list_for_contact(contact_id)
