"""DoD item 7: login gives identical responses for a wrong password and
an unknown email (no account-enumeration signal), and rejects an
inactive account — all with the same generic 401."""

import uuid
from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from tmis.core import database as core_database
from tmis.core.security import hash_password
from tmis.domain.firm.entities import Firm, SubscriptionPlan
from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email, Role
from tmis.infrastructure.persistence.models import UserModel
from tmis.infrastructure.persistence.repositories import (
    SqlAlchemyFirmRepository,
    SqlAlchemyUserRepository,
)


def test_successful_login_returns_token_pair(
    client: TestClient, register_user: Callable[..., Any], test_password: str
) -> None:
    user = register_user(email="lawyer@example.com")

    response = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": test_password}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


def test_wrong_password_and_unknown_email_return_identical_responses(
    client: TestClient, register_user: Callable[..., Any]
) -> None:
    user = register_user(email="lawyer@example.com")

    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "not-the-password"}
    )
    unknown_email = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_malformed_email_returns_the_same_generic_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "not-an-email", "password": "whatever"}
    )
    assert response.status_code == 401


def test_inactive_account_cannot_log_in(client: TestClient, test_password: str) -> None:
    session = core_database.SessionLocal()
    firm_id = uuid.uuid4()
    SqlAlchemyFirmRepository(session).add(
        Firm(id=firm_id, name="Cabinet inactif", plan=SubscriptionPlan.SOLO)
    )
    SqlAlchemyUserRepository(session).add(
        User(
            id=uuid.uuid4(),
            firm_id=firm_id,
            email=Email("suspended@example.com"),
            full_name="Suspended User",
            role=Role.LAWYER,
            hashed_password=hash_password(test_password),
            is_active=False,
        )
    )
    session.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "suspended@example.com", "password": test_password},
    )
    assert response.status_code == 401


def test_refresh_rotates_the_refresh_token(
    authenticated_session: Callable[..., Any], client: TestClient
) -> None:
    session = authenticated_session()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": session.refresh_token})

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != session.refresh_token
    assert new_tokens["access_token"] != session.access_token


def test_refresh_with_garbage_token_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401


def test_refresh_is_rejected_once_the_account_is_deactivated(
    authenticated_session: Callable[..., Any], client: TestClient
) -> None:
    """The refresh use case reloads the user from the repository rather
    than trusting the old token's claims — a still-unexpired refresh
    token from a since-deactivated account must not mint new ones."""
    session = authenticated_session()

    db_session = core_database.SessionLocal()
    user_model = db_session.get(UserModel, session.user.user_id)
    assert user_model is not None
    user_model.is_active = False
    db_session.commit()
    db_session.close()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": session.refresh_token})
    assert response.status_code == 401
