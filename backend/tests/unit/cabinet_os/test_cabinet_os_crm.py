import pytest

from tmis.cabinet_os.clients.schemas import ClientStatus, ClientType
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.clients.store import InMemoryClientStore
from tmis.cabinet_os.contacts.schemas import ContactRelationType, ContactRole
from tmis.cabinet_os.contacts.service import ContactService
from tmis.cabinet_os.contacts.store import InMemoryContactStore
from tmis.cabinet_os.crm.engine import CRMEngine


def test_create_individual_client_starts_as_prospect() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")

    assert client.status is ClientStatus.PROSPECT
    assert client.client_type is ClientType.INDIVIDUAL
    assert len(client.history) == 1


def test_create_organization_client_with_legal_fields() -> None:
    service = ClientService()
    client = service.create(
        "firm-1",
        ClientType.ORGANIZATION,
        "Acme SAS",
        legal_form="SAS",
        registration_number="123456789",
    )

    assert client.client_type is ClientType.ORGANIZATION
    assert client.legal_form == "SAS"


def test_change_status_activates_a_prospect() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")

    activated = service.change_status(client.id, ClientStatus.ACTIVE, actor_id="admin-1")

    assert activated.status is ClientStatus.ACTIVE
    assert len(activated.history) == 2


def test_cannot_reactivate_directly_from_prospect_to_prospect() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")

    with pytest.raises(ValueError, match="Cannot transition"):
        service.change_status(client.id, ClientStatus.PROSPECT)


def test_archived_client_can_be_reactivated() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")
    service.change_status(client.id, ClientStatus.ARCHIVED)

    reactivated = service.change_status(client.id, ClientStatus.ACTIVE)

    assert reactivated.status is ClientStatus.ACTIVE


def test_add_note_is_append_only() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")

    service.add_note(client.id, "author-1", "Premier contact")
    updated = service.add_note(client.id, "author-2", "Suivi")

    assert len(updated.notes) == 2
    assert updated.notes[0].text == "Premier contact"


def test_link_case_document_and_contact() -> None:
    service = ClientService()
    client = service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")

    service.link_case(client.id, "case-1")
    service.link_document(client.id, "doc-1")
    updated = service.link_contact(client.id, "contact-1")

    assert "case-1" in updated.case_ids
    assert "doc-1" in updated.document_ids
    assert "contact-1" in updated.contact_ids


def test_unknown_client_raises() -> None:
    service = ClientService()

    with pytest.raises(ValueError, match="Unknown client"):
        service.add_note("nope", "author-1", "text")


def test_contact_service_creates_contact_with_role() -> None:
    service = ContactService()
    contact = service.create("firm-1", ContactRole.EXPERT, "Dr. Martin")

    assert contact.role is ContactRole.EXPERT


def test_contact_relation_is_bidirectionally_listed() -> None:
    service = ContactService()
    a = service.create("firm-1", ContactRole.EXECUTIVE, "A")
    b = service.create("firm-1", ContactRole.REPRESENTATIVE, "B")

    service.relate("firm-1", a.id, b.id, ContactRelationType.REPRESENTS)

    assert len(service.list_relations(a.id)) == 1
    assert len(service.list_relations(b.id)) == 1


def test_crm_engine_get_profile_resolves_contacts_by_id() -> None:
    client_store = InMemoryClientStore()
    contact_store = InMemoryContactStore()
    client_service = ClientService(client_store)
    contact_service = ContactService(contact_store)
    crm = CRMEngine(client_store, contact_store)

    client = client_service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont")
    contact = contact_service.create("firm-1", ContactRole.WITNESS, "Témoin")
    client_service.link_contact(client.id, contact.id)
    client_service.link_case(client.id, "case-1")

    profile = crm.get_profile(client.id)

    assert profile.client.id == client.id
    assert profile.contacts == [contact]
    assert profile.case_ids == ["case-1"]


def test_crm_engine_get_profile_unknown_client_raises() -> None:
    crm = CRMEngine(InMemoryClientStore(), InMemoryContactStore())

    with pytest.raises(ValueError, match="Unknown client"):
        crm.get_profile("nope")


def test_crm_engine_search_matches_name_and_email() -> None:
    client_store = InMemoryClientStore()
    client_service = ClientService(client_store)
    crm = CRMEngine(client_store, InMemoryContactStore())

    client_service.create("firm-1", ClientType.INDIVIDUAL, "Jean Dupont", email="jean@x.fr")
    client_service.create("firm-1", ClientType.INDIVIDUAL, "Marie Curie", email="marie@x.fr")

    results = crm.search("firm-1", "jean")

    assert len(results) == 1
    assert results[0].display_name == "Jean Dupont"


def test_crm_engine_search_empty_query_returns_all_for_firm() -> None:
    client_store = InMemoryClientStore()
    client_service = ClientService(client_store)
    crm = CRMEngine(client_store, InMemoryContactStore())

    client_service.create("firm-1", ClientType.INDIVIDUAL, "A")
    client_service.create("firm-1", ClientType.INDIVIDUAL, "B")
    client_service.create("firm-2", ClientType.INDIVIDUAL, "C")

    assert len(crm.search("firm-1", "")) == 2
