"""DoD items 4 & 5: a tampered, `alg=none`, expired, or wrong-type token
is always rejected with a generic 401 — never a 500, never a message
that discloses which of those it was."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from tmis.core.config import get_settings

_PROTECTED_PATH = "/api/v1/cases"


def _authorized(client: TestClient, token: str) -> Any:
    return client.get(_PROTECTED_PATH, headers={"Authorization": f"Bearer {token}"})


def test_tampered_signature_is_rejected(
    authenticated_session: Callable[..., Any],
) -> None:
    session = authenticated_session()
    tampered = session.access_token[:-1] + ("A" if session.access_token[-1] != "A" else "B")
    assert _authorized(session.client, tampered).status_code == 401


def test_alg_none_token_is_rejected(client: TestClient) -> None:
    settings = get_settings()
    header = '{"alg":"none","typ":"JWT"}'
    import base64
    import json

    def _b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    payload = json.dumps(
        {
            "sub": str(uuid.uuid4()),
            "firm_id": str(uuid.uuid4()),
            "role": "platform_admin",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "token_type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        }
    ).encode()
    alg_none_token = f"{_b64(header.encode())}.{_b64(payload)}."

    assert _authorized(client, alg_none_token).status_code == 401


def test_expired_token_is_rejected(client: TestClient) -> None:
    settings = get_settings()
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "firm_id": str(uuid.uuid4()),
        "role": "lawyer",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "iat": datetime.now(UTC) - timedelta(minutes=20),
    }
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    assert _authorized(client, expired_token).status_code == 401


def test_refresh_token_presented_as_access_is_rejected(
    authenticated_session: Callable[..., Any],
) -> None:
    session = authenticated_session()
    assert _authorized(session.client, session.refresh_token).status_code == 401


def test_access_token_presented_as_refresh_is_rejected(
    authenticated_session: Callable[..., Any], client: TestClient
) -> None:
    session = authenticated_session()
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": session.access_token}
    )
    assert response.status_code == 401


def test_wrong_signing_secret_is_rejected(client: TestClient) -> None:
    settings = get_settings()
    forged_payload = {
        "sub": str(uuid.uuid4()),
        "firm_id": str(uuid.uuid4()),
        "role": "platform_admin",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    forged_token = jwt.encode(forged_payload, "a-completely-different-secret", algorithm="HS256")
    assert _authorized(client, forged_token).status_code == 401


@pytest.mark.parametrize("bad_claim", ["iss", "aud"])
def test_wrong_issuer_or_audience_is_rejected(client: TestClient, bad_claim: str) -> None:
    settings = get_settings()
    payload = {
        "sub": str(uuid.uuid4()),
        "firm_id": str(uuid.uuid4()),
        "role": "platform_admin",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "token_type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    payload[bad_claim] = "someone-elses-service"
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    assert _authorized(client, token).status_code == 401
