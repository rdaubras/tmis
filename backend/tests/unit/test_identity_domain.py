import uuid

import pytest

from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email, Permission, Role


def make_user(role: Role = Role.LAWYER) -> User:
    return User(
        id=uuid.uuid4(),
        firm_id=uuid.uuid4(),
        email=Email("avocat@example.com"),
        full_name="Jeanne Avocat",
        role=role,
        hashed_password="hashed",
    )


def test_email_rejects_invalid_format() -> None:
    with pytest.raises(ValueError):
        Email("not-an-email")


def test_lawyer_has_case_write_permission() -> None:
    user = make_user(Role.LAWYER)
    assert user.has_permission(Permission.CASE_WRITE)


def test_collaborator_cannot_manage_firm() -> None:
    user = make_user(Role.COLLABORATOR)
    assert not user.has_permission(Permission.FIRM_MANAGE)


def test_inactive_user_has_no_permission() -> None:
    user = make_user(Role.PLATFORM_ADMIN)
    user.is_active = False
    assert not user.has_permission(Permission.PLATFORM_MANAGE)
