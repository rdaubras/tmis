"""DoD item 2 & 3: cross-tenant access is impossible, and a client-
supplied `X-Firm-Id` header has no effect — tenant now comes only from
the validated access token (see `tmis.api.deps.get_current_firm_id`,
T4)."""

from collections.abc import Callable
from typing import Any


def _create_case(session: Any, title: str) -> str:
    response = session.client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def test_firm_b_cannot_list_firm_a_cases(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    _create_case(firm_a, "Dossier confidentiel A")

    assert firm_b.client.get("/api/v1/cases").json() == []
    assert len(firm_a.client.get("/api/v1/cases").json()) == 1


def test_firm_b_gets_404_reading_firm_a_case_by_id(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_id = _create_case(firm_a, "Dossier confidentiel A")

    response = firm_b.client.get(f"/api/v1/cases/{case_id}")
    assert response.status_code == 404
    # Never confirms the case exists under another tenant.
    assert "confidentiel" not in response.text

    assert firm_a.client.get(f"/api/v1/cases/{case_id}").status_code == 200


def test_isolation_is_symmetric(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    case_b = _create_case(firm_b, "Dossier B")

    assert firm_a.client.get(f"/api/v1/cases/{case_b}").status_code == 404
    assert firm_b.client.get(f"/api/v1/cases/{case_a}").status_code == 404


def test_x_firm_id_header_is_ignored(
    authenticated_session: Callable[..., Any],
) -> None:
    """Firm A's token with firm B's id spoofed in `X-Firm-Id`: the
    request stays scoped to firm A, exactly as if the header were never
    sent — there is no code path left that reads it (T4)."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    _create_case(firm_a, "Dossier A")

    response = firm_a.client.post(
        "/api/v1/cases",
        json={"title": "Second dossier A"},
        headers={"X-Firm-Id": str(firm_b.user.firm_id)},
    )
    assert response.status_code == 201
    assert response.json()["firm_id"] == str(firm_a.user.firm_id)

    # Firm B still sees nothing, despite its id being spoofed in the header.
    assert firm_b.client.get("/api/v1/cases").json() == []
    assert len(firm_a.client.get("/api/v1/cases").json()) == 2
