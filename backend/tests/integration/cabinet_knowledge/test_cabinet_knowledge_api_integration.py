from fastapi.testclient import TestClient

from tmis.main import app


def test_create_and_get_generic_object() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": "firm-api-1",
            "type": "note",
            "title": "Note de recherche",
            "content": {"text": "..."},
            "author": "avocat1",
        },
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert body["status"] == "draft"

    get_response = client.get(
        f"/api/v1/cabinet-knowledge/objects/{body['id']}", params={"firm_id": "firm-api-1"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Note de recherche"


def test_get_object_from_wrong_firm_returns_404() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": "firm-api-2",
            "type": "note",
            "title": "N",
            "content": {},
            "author": "a",
        },
    ).json()

    response = client.get(
        f"/api/v1/cabinet-knowledge/objects/{created['id']}", params={"firm_id": "other-firm"}
    )

    assert response.status_code == 404


def test_playbook_create_validate_publish_and_instantiate() -> None:
    client = TestClient(app)
    firm_id = "firm-api-3"

    playbook = client.post(
        "/api/v1/cabinet-knowledge/playbooks",
        json={
            "firm_id": firm_id,
            "title": "Ouverture prud'homale",
            "case_type": "prudhommes",
            "steps": [
                {"order": 1, "title": "Entretien", "description": "..."},
                {"order": 2, "title": "Dossier", "description": "..."},
            ],
            "checklist": ["Vérifier délai"],
            "author": "avocat1",
        },
    ).json()

    start_before_validation = client.post(
        f"/api/v1/cabinet-knowledge/playbooks/{playbook['id']}/instances",
        json={"firm_id": firm_id, "case_reference": "dossier-1"},
    )
    assert start_before_validation.status_code == 400

    submitted = client.post(
        f"/api/v1/cabinet-knowledge/objects/{playbook['id']}/submit-for-validation",
        json={"firm_id": firm_id, "requested_by": "avocat1"},
    ).json()
    client.post(
        f"/api/v1/cabinet-knowledge/validation-requests/{submitted['id']}/decide",
        json={"firm_id": firm_id, "decision": "approve", "reviewer": "associe1"},
    )
    client.post(
        f"/api/v1/cabinet-knowledge/objects/{playbook['id']}/publish",
        json={"firm_id": firm_id, "approver": "associe1"},
    )

    instance = client.post(
        f"/api/v1/cabinet-knowledge/playbooks/{playbook['id']}/instances",
        json={"firm_id": firm_id, "case_reference": "dossier-1"},
    )
    assert instance.status_code == 200
    instance_body = instance.json()
    assert instance_body["progress"] == 0.0

    completed = client.post(
        f"/api/v1/cabinet-knowledge/playbook-instances/{instance_body['id']}/steps/1/complete",
        params={"firm_id": firm_id},
    )
    assert completed.status_code == 200
    assert completed.json()["progress"] == 0.5


def test_search_and_recommendations_only_surface_published_objects() -> None:
    client = TestClient(app)
    firm_id = "firm-api-4"

    clause = client.post(
        "/api/v1/cabinet-knowledge/clauses",
        json={
            "firm_id": firm_id,
            "title": "Non-concurrence",
            "domain": "commercial",
            "clause_type": "non_concurrence",
            "variants": [{"id": "v1", "text": "Interdiction de concurrence pendant 2 ans"}],
            "author": "avocat1",
        },
    ).json()

    unpublished_search = client.post(
        "/api/v1/cabinet-knowledge/search",
        json={"firm_id": firm_id, "published_only": True},
    ).json()
    assert clause["id"] not in [o["id"] for o in unpublished_search]

    submitted = client.post(
        f"/api/v1/cabinet-knowledge/objects/{clause['id']}/submit-for-validation",
        json={"firm_id": firm_id, "requested_by": "avocat1"},
    ).json()
    client.post(
        f"/api/v1/cabinet-knowledge/validation-requests/{submitted['id']}/decide",
        json={"firm_id": firm_id, "decision": "approve", "reviewer": "associe1"},
    )
    client.post(
        f"/api/v1/cabinet-knowledge/objects/{clause['id']}/publish",
        json={"firm_id": firm_id, "approver": "associe1"},
    )

    published_search = client.post(
        "/api/v1/cabinet-knowledge/search",
        json={"firm_id": firm_id, "published_only": True},
    ).json()
    assert clause["id"] in [o["id"] for o in published_search]

    recommendations = client.post(
        "/api/v1/cabinet-knowledge/recommendations",
        json={"firm_id": firm_id, "keywords": ["concurrence"]},
    ).json()
    assert clause["id"] in [r["knowledge_object_id"] for r in recommendations]
    assert all(r["explanation"] for r in recommendations)


def test_feedback_and_evaluation_endpoints() -> None:
    client = TestClient(app)
    firm_id = "firm-api-5"

    obj = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": firm_id,
            "type": "note",
            "title": "N",
            "content": {},
            "author": "a",
        },
    ).json()

    feedback = client.post(
        "/api/v1/cabinet-knowledge/feedback",
        json={
            "firm_id": firm_id,
            "knowledge_object_id": obj["id"],
            "action": "accept",
            "author": "avocat2",
            "comment": "bien vu",
        },
    )
    assert feedback.status_code == 200

    history = client.get(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/feedback", params={"firm_id": firm_id}
    )
    assert len(history.json()) == 1

    evaluation = client.get(
        "/api/v1/cabinet-knowledge/evaluation", params={"firm_id": firm_id}
    )
    assert evaluation.status_code == 200
    assert evaluation.json()["total_objects"] == 1


def test_unknown_decision_type_returns_400() -> None:
    client = TestClient(app)
    firm_id = "firm-api-6"
    obj = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": firm_id,
            "type": "note",
            "title": "N",
            "content": {},
            "author": "a",
        },
    ).json()
    submitted = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/submit-for-validation",
        json={"firm_id": firm_id, "requested_by": "a"},
    ).json()

    response = client.post(
        f"/api/v1/cabinet-knowledge/validation-requests/{submitted['id']}/decide",
        json={"firm_id": firm_id, "decision": "not-a-real-decision", "reviewer": "b"},
    )

    assert response.status_code == 400
