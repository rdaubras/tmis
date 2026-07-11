from fastapi.testclient import TestClient

from tmis.main import app


def test_strategy_generation_lifecycle_via_api() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/strategic-intelligence/strategies/generate",
        json={
            "case_id": "case-api-1",
            "question": "Comment défendre ce salarié ?",
            "hypotheses": ["Licenciement sans cause réelle et sérieuse"],
            "available_evidence": ["Bulletins de salaire"],
            "missing_evidence": ["Témoignage collègue"],
        },
    )

    assert response.status_code == 200
    strategies = response.json()
    assert len(strategies) == 4
    for strategy in strategies:
        assert strategy["limitations"]


def test_hypothesis_lab_lifecycle_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/strategic-intelligence/hypotheses",
        json={"firm_id": "firm-api-hyp", "case_id": "case-api-hyp", "description": "Hypothèse A"},
    )
    assert created.status_code == 200
    hyp_id = created.json()["id"]
    assert created.json()["status"] == "proposed"

    listed = client.get(
        "/api/v1/strategic-intelligence/hypotheses/case-api-hyp",
        params={"firm_id": "firm-api-hyp"},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    archived = client.post(
        f"/api/v1/strategic-intelligence/hypotheses/{hyp_id}/archive",
        json={"firm_id": "firm-api-hyp", "actor": "avocat-1", "reason": "clôture"},
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    history = client.get(
        f"/api/v1/strategic-intelligence/hypotheses/{hyp_id}/history",
        params={"firm_id": "firm-api-hyp"},
    )
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_action_plan_and_strategy_overview_via_api() -> None:
    client = TestClient(app)

    step = client.post(
        "/api/v1/strategic-intelligence/action-plan/steps",
        json={
            "firm_id": "firm-api-plan",
            "strategy_id": "strategy-api-plan",
            "description": "Envoyer mise en demeure",
            "category": "procédure",
        },
    )
    assert step.status_code == 200

    overview = client.get(
        "/api/v1/strategic-intelligence/overview/strategy/strategy-api-plan",
        params={"firm_id": "firm-api-plan"},
    )
    assert overview.status_code == 200
    body = overview.json()
    assert len(body["action_steps"]) == 1
    assert body["is_validated"] is False


def test_review_workflow_via_api() -> None:
    client = TestClient(app)

    request = client.post(
        "/api/v1/strategic-intelligence/review/request",
        json={
            "firm_id": "firm-api-review",
            "strategy_id": "strategy-api-review",
            "requested_by": "avocat-1",
            "approver_ids": ["associe-1"],
        },
    )
    assert request.status_code == 200
    request_id = request.json()["id"]

    decided = client.post(
        f"/api/v1/strategic-intelligence/review/{request_id}/decide",
        json={"firm_id": "firm-api-review", "approver_id": "associe-1", "decision": "approve"},
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"


def test_decision_support_never_returns_a_winner_field_via_api() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/strategic-intelligence/decision-support/compare",
        json={
            "metrics": [
                {
                    "strategy_id": "strategy-1",
                    "strategy_type": "Négociation amiable",
                    "confidence": 0.6,
                    "coverage": 0.7,
                    "risk_score": 0.3,
                    "effort": 0.4,
                    "estimated_duration_days": 30,
                }
            ]
        },
    )

    assert response.status_code == 200
    assert "winner" not in response.json()
    assert "recommended" not in response.json()
    assert response.json()["disclaimer"]


def test_simulation_never_returns_a_prediction_field_via_api() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/strategic-intelligence/simulation/run",
        json={
            "base_case_id": "case-api-sim",
            "strategy_texts": {"strategy-1": "Fondée sur le témoignage"},
            "hypothetical_changes": ["témoignage"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "prediction" not in body
    assert "win_probability" not in body
    assert body["affected_strategy_ids"] == ["strategy-1"]
