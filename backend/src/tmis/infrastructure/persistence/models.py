import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tmis.core.database import Base
from tmis.domain.case.entities import CaseStatus
from tmis.domain.firm.entities import SubscriptionPlan
from tmis.domain.identity.value_objects import Role


class FirmModel(Base):
    __tablename__ = "firms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(nullable=False, default=SubscriptionPlan.SOLO)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["UserModel"]] = relationship(back_populates="firm")
    cases: Mapped[list["CaseModel"]] = relationship(back_populates="firm")


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("firms.id"), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[Role] = mapped_column(nullable=False, default=Role.LAWYER)
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    firm: Mapped[FirmModel] = relationship(back_populates="users")


class CaseModel(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[CaseStatus] = mapped_column(nullable=False, default=CaseStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    firm: Mapped[FirmModel] = relationship(back_populates="cases")
