import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from tmis.core.tenancy import scoped_query
from tmis.domain.case.entities import Case
from tmis.domain.firm.entities import Firm
from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email
from tmis.infrastructure.persistence.models import CaseModel, FirmModel, UserModel


def _case_to_entity(model: CaseModel) -> Case:
    return Case(id=model.id, firm_id=model.firm_id, title=model.title, status=model.status)


def _firm_to_entity(model: FirmModel) -> Firm:
    return Firm(id=model.id, name=model.name, plan=model.plan, is_active=model.is_active)


def _user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        firm_id=model.firm_id,
        email=Email(model.email),
        full_name=model.full_name,
        role=model.role,
        hashed_password=model.hashed_password,
        mfa_enabled=model.mfa_enabled,
        is_active=model.is_active,
    )


class SqlAlchemyCaseRepository:
    """Implements `tmis.domain.case.ports.CaseRepositoryPort`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, case_id: uuid.UUID, firm_id: uuid.UUID) -> Case | None:
        stmt = scoped_query(CaseModel, firm_id).where(CaseModel.id == case_id)
        model = self._session.scalar(stmt)
        return _case_to_entity(model) if model else None

    def list_by_firm(self, firm_id: uuid.UUID) -> list[Case]:
        stmt = scoped_query(CaseModel, firm_id)
        return [_case_to_entity(m) for m in self._session.scalars(stmt)]

    def add(self, case: Case) -> None:
        self._session.add(
            CaseModel(id=case.id, firm_id=case.firm_id, title=case.title, status=case.status)
        )
        self._session.commit()


class SqlAlchemyUserRepository:
    """Implements `tmis.domain.identity.ports.UserRepositoryPort`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: uuid.UUID, firm_id: uuid.UUID) -> User | None:
        stmt = scoped_query(UserModel, firm_id).where(UserModel.id == user_id)
        model = self._session.scalar(stmt)
        return _user_to_entity(model) if model else None

    def get_by_email(self, email: Email) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.value)
        model = self._session.scalar(stmt)
        return _user_to_entity(model) if model else None

    def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                firm_id=user.firm_id,
                email=user.email.value,
                full_name=user.full_name,
                hashed_password=user.hashed_password,
                role=user.role,
                mfa_enabled=user.mfa_enabled,
                is_active=user.is_active,
            )
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
