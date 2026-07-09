import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from tmis.domain.case.entities import Case
from tmis.domain.firm.entities import Firm
from tmis.infrastructure.persistence.models import CaseModel, FirmModel


def _case_to_entity(model: CaseModel) -> Case:
    return Case(id=model.id, firm_id=model.firm_id, title=model.title, status=model.status)


def _firm_to_entity(model: FirmModel) -> Firm:
    return Firm(id=model.id, name=model.name, plan=model.plan, is_active=model.is_active)


class SqlAlchemyCaseRepository:
    """Implements `tmis.domain.case.ports.CaseRepositoryPort`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, case_id: uuid.UUID, firm_id: uuid.UUID) -> Case | None:
        stmt = select(CaseModel).where(CaseModel.id == case_id, CaseModel.firm_id == firm_id)
        model = self._session.scalar(stmt)
        return _case_to_entity(model) if model else None

    def list_by_firm(self, firm_id: uuid.UUID) -> list[Case]:
        stmt = select(CaseModel).where(CaseModel.firm_id == firm_id)
        return [_case_to_entity(m) for m in self._session.scalars(stmt)]

    def add(self, case: Case) -> None:
        self._session.add(
            CaseModel(id=case.id, firm_id=case.firm_id, title=case.title, status=case.status)
        )
        self._session.commit()


class SqlAlchemyFirmRepository:
    """Implements `tmis.domain.firm.ports.FirmRepositoryPort`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, firm_id: uuid.UUID) -> Firm | None:
        model = self._session.get(FirmModel, firm_id)
        return _firm_to_entity(model) if model else None

    def add(self, firm: Firm) -> None:
        self._session.add(
            FirmModel(id=firm.id, name=firm.name, plan=firm.plan, is_active=firm.is_active)
        )
        self._session.commit()
