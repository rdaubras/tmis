from fastapi import APIRouter, Depends, HTTPException

from tmis.cabinet_os.api.schemas import (
    AddClientNoteRequest,
    ChangeClientStatusRequest,
    ClientResponse,
    ContactResponse,
    CreateClientRequest,
    CreateContactRequest,
)
from tmis.cabinet_os.bootstrap import get_client_service, get_contact_service, get_crm_engine
from tmis.cabinet_os.clients.schemas import Client, ClientStatus, ClientType
from tmis.cabinet_os.clients.service import ClientService
from tmis.cabinet_os.contacts.schemas import Contact, ContactRole
from tmis.cabinet_os.contacts.service import ContactService
from tmis.cabinet_os.crm.engine import CRMEngine

router = APIRouter(prefix="/cabinet-os", tags=["cabinet-os-crm"])


def _to_client_response(client: Client) -> ClientResponse:
    return ClientResponse(
        id=client.id,
        firm_id=client.firm_id,
        client_type=client.client_type.value,
        display_name=client.display_name,
        email=client.email,
        phone=client.phone,
        status=client.status.value,
        case_ids=list(client.case_ids),
        document_ids=list(client.document_ids),
        contact_ids=list(client.contact_ids),
    )


def _to_contact_response(contact: Contact) -> ContactResponse:
    return ContactResponse(
        id=contact.id,
        firm_id=contact.firm_id,
        role=contact.role.value,
        display_name=contact.display_name,
        email=contact.email,
        phone=contact.phone,
    )


@router.post("/clients", response_model=ClientResponse)
def create_client(
    payload: CreateClientRequest,
    service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        client_type = ClientType(payload.client_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown client type: {payload.client_type!r}"
        ) from exc
    client = service.create(
        payload.firm_id,
        client_type,
        payload.display_name,
        email=payload.email,
        phone=payload.phone,
        first_name=payload.first_name,
        last_name=payload.last_name,
        legal_form=payload.legal_form,
        registration_number=payload.registration_number,
    )
    return _to_client_response(client)


@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: str, crm: CRMEngine = Depends(get_crm_engine)) -> ClientResponse:
    try:
        profile = crm.get_profile(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_client_response(profile.client)


@router.get("/clients", response_model=list[ClientResponse])
def search_clients(
    firm_id: str, q: str = "", crm: CRMEngine = Depends(get_crm_engine)
) -> list[ClientResponse]:
    return [_to_client_response(c) for c in crm.search(firm_id, q)]


@router.post("/clients/{client_id}/notes", response_model=ClientResponse)
def add_client_note(
    client_id: str,
    payload: AddClientNoteRequest,
    service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        client = service.add_note(client_id, payload.author_id, payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_client_response(client)


@router.post("/clients/{client_id}/status", response_model=ClientResponse)
def change_client_status(
    client_id: str,
    payload: ChangeClientStatusRequest,
    service: ClientService = Depends(get_client_service),
) -> ClientResponse:
    try:
        target = ClientStatus(payload.target)
        client = service.change_status(client_id, target, payload.actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_client_response(client)


@router.post("/contacts", response_model=ContactResponse)
def create_contact(
    payload: CreateContactRequest,
    service: ContactService = Depends(get_contact_service),
) -> ContactResponse:
    try:
        role = ContactRole(payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown contact role: {payload.role!r}"
        ) from exc
    contact = service.create(
        payload.firm_id,
        role,
        payload.display_name,
        email=payload.email,
        phone=payload.phone,
        organization_client_id=payload.organization_client_id,
    )
    return _to_contact_response(contact)
