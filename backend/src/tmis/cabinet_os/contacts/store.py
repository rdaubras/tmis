from tmis.cabinet_os.contacts.schemas import Contact, ContactRelation


class InMemoryContactStore:
    """Implements `ContactStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._contacts: dict[str, Contact] = {}

    def get(self, contact_id: str) -> Contact | None:
        return self._contacts.get(contact_id)

    def save(self, contact: Contact) -> None:
        self._contacts[contact.id] = contact

    def list_for_firm(self, firm_id: str) -> list[Contact]:
        return [c for c in self._contacts.values() if c.firm_id == firm_id]


class InMemoryContactRelationStore:
    """Implements `ContactRelationStorePort` with an in-memory list —
    relations are directed, so a contact can appear as either source or
    target of several relations."""

    def __init__(self) -> None:
        self._relations: list[ContactRelation] = []

    def save(self, relation: ContactRelation) -> None:
        self._relations.append(relation)

    def list_for_contact(self, contact_id: str) -> list[ContactRelation]:
        return [
            r
            for r in self._relations
            if r.source_contact_id == contact_id or r.target_contact_id == contact_id
        ]
