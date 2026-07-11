from fastapi.testclient import TestClient

from tmis.main import app


def test_list_objects_and_history_and_lineage_and_quality() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-1"

    obj = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": firm_id,
            "type": "note",
            "title": "N",
            "content": {"text": "..."},
            "author": "a",
            "tags": ["rgpd"],
        },
    ).json()

    listed = client.get(
        "/api/v1/cabinet-knowledge/objects",
        params={"firm_id": firm_id, "type": "note", "status": "draft"},
    )
    assert listed.status_code == 200
    assert obj["id"] in [o["id"] for o in listed.json()]

    submitted = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/submit-for-validation",
        json={"firm_id": firm_id, "requested_by": "a"},
    ).json()

    pending = client.get(
        "/api/v1/cabinet-knowledge/validation-requests", params={"firm_id": firm_id}
    )
    assert submitted["id"] in [r["id"] for r in pending.json()]

    history = client.get(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/history", params={"firm_id": firm_id}
    )
    assert history.status_code == 200
    assert history.json()[0]["to_status"] == "in_review"

    lineage = client.get(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/lineage", params={"firm_id": firm_id}
    )
    assert lineage.status_code == 200
    assert lineage.json()["current_version"] == 1

    quality = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/quality", params={"firm_id": firm_id}
    )
    assert quality.status_code == 200
    assert quality.json()["quality_score"] >= 0.0


def test_lineage_for_unknown_object_returns_404() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/cabinet-knowledge/objects/unknown-id/lineage",
        params={"firm_id": "firm-api-remaining-2"},
    )

    assert response.status_code == 404


def test_templates_create_and_list() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-3"

    created = client.post(
        "/api/v1/cabinet-knowledge/templates",
        json={
            "firm_id": firm_id,
            "title": "Mise en demeure standard",
            "document_type": "mise_en_demeure",
            "structure": ["header", "facts"],
            "author": "a",
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/api/v1/cabinet-knowledge/templates",
        params={"firm_id": firm_id, "document_type": "mise_en_demeure"},
    )
    assert len(listed.json()) == 1


def test_reasoning_patterns_create_and_list() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-4"

    created = client.post(
        "/api/v1/cabinet-knowledge/reasoning-patterns",
        json={
            "firm_id": firm_id,
            "title": "Prescription prud'homale",
            "context": "licenciement délai",
            "strategy": "invoquer la prescription",
            "arguments": ["Article L1471-1"],
            "author": "a",
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/api/v1/cabinet-knowledge/reasoning-patterns", params={"firm_id": firm_id}
    )
    assert len(listed.json()) == 1


def test_writing_style_get_and_update() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-5"

    initial = client.get(
        "/api/v1/cabinet-knowledge/writing-style", params={"firm_id": firm_id, "actor": "a"}
    )
    assert initial.status_code == 200
    assert initial.json()["signature_block"] == ""

    updated = client.put(
        "/api/v1/cabinet-knowledge/writing-style",
        json={"firm_id": firm_id, "actor": "a", "signature_block": "Bien cordialement,"},
    )
    assert updated.status_code == 200
    assert updated.json()["signature_block"] == "Bien cordialement,"


def test_best_practices_create_and_list() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-6"

    created = client.post(
        "/api/v1/cabinet-knowledge/best-practices",
        json={
            "firm_id": firm_id,
            "title": "Vérifier les délais",
            "description": "...",
            "domain": "civil",
            "source": "interne",
            "author": "a",
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/api/v1/cabinet-knowledge/best-practices", params={"firm_id": firm_id, "domain": "civil"}
    )
    assert len(listed.json()) == 1


def test_lessons_learned_create_and_list() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-7"

    created = client.post(
        "/api/v1/cabinet-knowledge/lessons-learned",
        json={
            "firm_id": firm_id,
            "title": "Délai manqué",
            "context": "dossier X",
            "outcome": "forclusion",
            "recommendation": "vérifier les délais",
            "author": "a",
        },
    )
    assert created.status_code == 200

    listed = client.get(
        "/api/v1/cabinet-knowledge/lessons-learned",
        params={"firm_id": firm_id, "keyword": "délai"},
    )
    assert len(listed.json()) == 1


def test_clause_get_by_id_marks_usage() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-8"
    clause = client.post(
        "/api/v1/cabinet-knowledge/clauses",
        json={
            "firm_id": firm_id,
            "title": "Confidentialité",
            "domain": "commercial",
            "clause_type": "confidentialite",
            "variants": [{"id": "v1", "text": "Obligation de confidentialité"}],
            "author": "a",
        },
    ).json()

    fetched = client.get(
        f"/api/v1/cabinet-knowledge/clauses/{clause['id']}", params={"firm_id": firm_id}
    )
    assert fetched.status_code == 200

    unknown = client.get(
        "/api/v1/cabinet-knowledge/clauses/unknown-id", params={"firm_id": firm_id}
    )
    assert unknown.status_code == 404


def test_playbook_get_by_id_and_unknown_returns_404() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-9"
    playbook = client.post(
        "/api/v1/cabinet-knowledge/playbooks",
        json={
            "firm_id": firm_id,
            "title": "A",
            "case_type": "recouvrement",
            "steps": [{"order": 1, "title": "Etape", "description": "..."}],
            "author": "a",
        },
    ).json()

    fetched = client.get(
        f"/api/v1/cabinet-knowledge/playbooks/{playbook['id']}", params={"firm_id": firm_id}
    )
    assert fetched.status_code == 200

    unknown = client.get(
        "/api/v1/cabinet-knowledge/playbooks/unknown-id", params={"firm_id": firm_id}
    )
    assert unknown.status_code == 404


def test_validation_decide_on_unknown_request_returns_404() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/cabinet-knowledge/validation-requests/unknown/decide",
        json={"firm_id": "firm-api-remaining-10", "decision": "approve", "reviewer": "a"},
    )

    assert response.status_code == 404


def test_publish_unvalidated_object_returns_400() -> None:
    client = TestClient(app)
    firm_id = "firm-api-remaining-11"
    obj = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={"firm_id": firm_id, "type": "note", "title": "N", "content": {}, "author": "a"},
    ).json()

    response = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj['id']}/publish",
        json={"firm_id": firm_id, "approver": "a"},
    )

    assert response.status_code == 400


def test_unknown_object_type_returns_400() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/cabinet-knowledge/objects",
        json={
            "firm_id": "firm-api-remaining-12",
            "type": "not-a-real-type",
            "title": "N",
            "content": {},
            "author": "a",
        },
    )

    assert response.status_code == 400
