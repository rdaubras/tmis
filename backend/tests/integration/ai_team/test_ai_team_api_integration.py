from fastapi.testclient import TestClient

from tmis.main import app


def test_list_agents_returns_the_default_catalog() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-team/agents")

    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 10
    assert {a["role"] for a in agents} >= {"document_analyst", "verifier", "quality_controller"}


def test_create_team_auto_composes_from_domain_and_case_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-team/teams",
        json={"domain": "data_protection", "case_type": "standard_analysis"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "agent-gdpr-expert" in body["member_agent_ids"]
    assert body["is_custom"] is False


def test_create_custom_team() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-team/teams/custom",
        json={"name": "Mon équipe", "agent_ids": ["agent-drafter", "agent-verifier"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_custom"] is True
    assert body["member_agent_ids"] == ["agent-drafter", "agent-verifier"]


def test_launching_a_mission_against_an_unknown_team_returns_404() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "test",
            "team_id": "does-not-exist",
            "case_type": "quick_review",
        },
    )

    assert response.status_code == 404


def test_full_mission_lifecycle_through_the_api() -> None:
    client = TestClient(app)

    team_response = client.post("/api/v1/ai-team/teams", json={"case_type": "quick_review"})
    team_id = team_response.json()["id"]

    mission_response = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "Vérifie ce brouillon",
            "team_id": team_id,
            "case_type": "quick_review",
        },
    )
    assert mission_response.status_code == 200
    mission_id = mission_response.json()["id"]
    assert mission_response.json()["status"] == "created"

    run_response = client.post(f"/api/v1/ai-team/missions/{mission_id}/run")
    assert run_response.status_code == 200
    assert run_response.json()["status"] == "completed"

    results_response = client.get(f"/api/v1/ai-team/missions/{mission_id}/results")
    assert results_response.status_code == 200
    results_body = results_response.json()
    assert results_body["synthesis"] is not None
    assert len(results_body["results"]) == 2

    metrics_response = client.get(f"/api/v1/ai-team/missions/{mission_id}/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["agent_runs"] == 2


def test_human_decision_approve_via_api() -> None:
    client = TestClient(app)
    team_id = client.post("/api/v1/ai-team/teams", json={"case_type": "quick_review"}).json()["id"]
    mission_id = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "test",
            "team_id": team_id,
            "case_type": "quick_review",
        },
    ).json()["id"]

    response = client.post(
        f"/api/v1/ai-team/missions/{mission_id}/human-decisions",
        json={"actor_id": "lawyer-1", "decision_type": "approve"},
    )

    assert response.status_code == 200
    assert response.json()["decision_type"] == "approve"


def test_human_decision_exclude_agent_requires_agent_id() -> None:
    client = TestClient(app)
    team_id = client.post("/api/v1/ai-team/teams", json={"case_type": "quick_review"}).json()["id"]
    mission_id = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "test",
            "team_id": team_id,
            "case_type": "quick_review",
        },
    ).json()["id"]

    response = client.post(
        f"/api/v1/ai-team/missions/{mission_id}/human-decisions",
        json={"actor_id": "lawyer-1", "decision_type": "exclude_agent"},
    )

    assert response.status_code == 400


def test_human_decision_with_unknown_decision_type_returns_400() -> None:
    client = TestClient(app)
    team_id = client.post("/api/v1/ai-team/teams", json={"case_type": "quick_review"}).json()["id"]
    mission_id = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "test",
            "team_id": team_id,
            "case_type": "quick_review",
        },
    ).json()["id"]

    response = client.post(
        f"/api/v1/ai-team/missions/{mission_id}/human-decisions",
        json={"actor_id": "lawyer-1", "decision_type": "not-a-real-type"},
    )

    assert response.status_code == 400


def test_dashboard_reflects_launched_missions() -> None:
    client = TestClient(app)
    team_id = client.post("/api/v1/ai-team/teams", json={"case_type": "quick_review"}).json()["id"]
    client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": "firm-1",
            "request_description": "test",
            "team_id": team_id,
            "case_type": "quick_review",
        },
    )

    response = client.get("/api/v1/ai-team/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["total_missions"] >= 1


def test_get_mission_returns_404_for_unknown_mission() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-team/missions/does-not-exist")

    assert response.status_code == 404
