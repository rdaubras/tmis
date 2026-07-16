"""Shared fixtures for `tests/security/` — the sprint's Definition of
Done suite (see docs/07-strategie-securite.md). Every test here talks to
the real app through `TestClient`, with real, signed JWTs minted through
the real `/auth/login` endpoint or `tmis.core.security` directly — never
a `dependency_overrides` bypass. That is deliberate: this suite exists to
prove the auth boundary itself works, so nothing here may skip it.
"""

import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
from tmis.core import database as core_database
from tmis.core.security import hash_password
from tmis.domain.firm.entities import Firm, SubscriptionPlan
from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email, Role
from tmis.infrastructure.persistence.repositories import (
    SqlAlchemyFirmRepository,
    SqlAlchemyUserRepository,
)
from tmis.main import app

TEST_PASSWORD = "correct horse battery staple"


@pytest.fixture
def test_password() -> str:
    return TEST_PASSWORD


@pytest.fixture(autouse=True)
def _sqlite_database(tmp_path: object) -> Iterator[None]:
    """Points the shared sync engine (`tmis.core.database`) — used by
    `domain.case`/`domain.firm`/`domain.identity`'s SQLAlchemy adapters —
    at a throwaway per-test sqlite database, same pattern already used by
    `tests/integration/case_intelligence/test_case_api.py`."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/security.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_database.SessionLocal.configure(bind=engine)
    core_database.Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@dataclass(frozen=True, slots=True)
class RegisteredUser:
    firm_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    password: str


def _register_user(email: str, role: Role, firm_name: str) -> RegisteredUser:
    session = core_database.SessionLocal()
    try:
        firm_id = uuid.uuid4()
        SqlAlchemyFirmRepository(session).add(
            Firm(id=firm_id, name=firm_name, plan=SubscriptionPlan.CABINET)
        )
        user_id = uuid.uuid4()
        SqlAlchemyUserRepository(session).add(
            User(
                id=user_id,
                firm_id=firm_id,
                email=Email(email),
                full_name="Test User",
                role=role,
                hashed_password=hash_password(TEST_PASSWORD),
            )
        )
    finally:
        session.close()
    return RegisteredUser(firm_id=firm_id, user_id=user_id, email=email, password=TEST_PASSWORD)


@pytest.fixture
def register_user() -> Callable[..., RegisteredUser]:
    """Inserts a firm + active user straight through the real
    SQLAlchemy repositories — not a fixture shortcut around them."""

    def _make(
        email: str = "user@example.com",
        role: Role = Role.LAWYER,
        firm_name: str = "Cabinet de test",
    ) -> RegisteredUser:
        return _register_user(email, role, firm_name)

    return _make


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    client: TestClient
    user: RegisteredUser
    access_token: str
    refresh_token: str


@pytest.fixture
def authenticated_session(
    client: TestClient, register_user: Callable[..., RegisteredUser]
) -> Callable[..., AuthenticatedSession]:
    """`authenticated_client(firm_id)` from the sprint's own risk section
    (docs/07-strategie-securite.md §8) — registers a user and logs them
    in through the real `/auth/login` endpoint, returning a `TestClient`
    that carries a genuine access token by default."""

    def _make(
        email: str = "user@example.com",
        role: Role = Role.LAWYER,
        firm_name: str = "Cabinet de test",
    ) -> AuthenticatedSession:
        user = register_user(email=email, role=role, firm_name=firm_name)
        response = client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": user.password}
        )
        assert response.status_code == 200, response.text
        tokens = response.json()
        authed_client = TestClient(
            app, headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        return AuthenticatedSession(
            client=authed_client,
            user=user,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    return _make
