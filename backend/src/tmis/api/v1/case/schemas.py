import uuid

from pydantic import BaseModel

from tmis.domain.case.entities import CaseStatus


class CaseCreateRequest(BaseModel):
    title: str


class CaseResponse(BaseModel):
    id: uuid.UUID
    firm_id: uuid.UUID
    title: str
    status: CaseStatus
