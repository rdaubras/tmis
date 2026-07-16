import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tmis.api.deps import get_current_firm_id
from tmis.api.v1.case.schemas import CaseCreateRequest, CaseResponse
from tmis.application.case.commands import CreateCaseCommand, CreateCaseUseCase
from tmis.application.case.queries import ListCasesQuery, ListCasesUseCase
from tmis.core.database import get_db_session
from tmis.infrastructure.persistence.repositories import SqlAlchemyCaseRepository

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(
    payload: CaseCreateRequest,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
) -> CaseResponse:
    use_case = CreateCaseUseCase(SqlAlchemyCaseRepository(session))
    case = use_case.execute(CreateCaseCommand(firm_id=firm_id, title=payload.title))
    return CaseResponse(id=case.id, firm_id=case.firm_id, title=case.title, status=case.status)


@router.get("", response_model=list[CaseResponse])
def list_cases(
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
) -> list[CaseResponse]:
    use_case = ListCasesUseCase(SqlAlchemyCaseRepository(session))
    cases = use_case.execute(ListCasesQuery(firm_id=firm_id))
    return [
        CaseResponse(id=c.id, firm_id=c.firm_id, title=c.title, status=c.status) for c in cases
    ]


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
) -> CaseResponse:
    repository = SqlAlchemyCaseRepository(session)
    case = repository.get_by_id(case_id, firm_id)
    if case is None:
        # Same 404 whether the case belongs to another firm or doesn't
        # exist at all — never confirms a cross-tenant case's existence.
        raise HTTPException(status_code=404, detail="Dossier introuvable.")
    return CaseResponse(id=case.id, firm_id=case.firm_id, title=case.title, status=case.status)
