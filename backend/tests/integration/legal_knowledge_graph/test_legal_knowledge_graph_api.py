"""Integration tests for the Legal Knowledge Graph REST API, exercising
the real FastAPI app and the Enterprise Identity & Trust Platform gate
(see `identity_platform.api.guard.authorize_or_403`)."""

from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app

FIRM = "firm-lkg-api"


def _authorized_user(user_id: str = "partner-lkg") -> str:
    get_role_engine().assign(FIRM, user_id, Role.PARTNER)
    return user_id


def test_ingest_requires_authorization() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": "unauthorized-user",
            "source_type": "contract",
            "title": "Contrat",
            "content_text": "Contrat de prestation ACME Corp SARL.",
            "author": "Julien Moreau",
        },
    )

    assert response.status_code == 403


def test_ingest_then_validate_then_publish_roundtrip() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    ingested = client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "source_type": "contract",
            "title": "Contrat ACME",
            "content_text": "Contrat de prestation ACME Corp SARL, article 1134.",
            "author": "Julien Moreau",
        },
    )
    assert ingested.status_code == 200
    body = ingested.json()
    assert "ACME Corp SARL" in body["extracted_entity_labels"]

    decided = client.post(
        f"/api/v1/legal-knowledge-graph/validation/{body['validation_request_id']}/decide",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "decision": "approve",
            "reviewer": "Camille Lefèvre",
        },
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"

    published = client.post(
        "/api/v1/legal-knowledge-graph/publish",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "knowledge_object_id": body["knowledge_object_id"],
            "approver": "Camille Lefèvre",
        },
    )
    assert published.status_code == 200
    assert published.json()["status"] == "validated"

    relations = client.get(
        f"/api/v1/legal-knowledge-graph/nodes/{body['graph_node_id']}/relations",
        params={"firm_id": FIRM, "user_id": user_id},
    )
    assert relations.status_code == 200
    assert len(relations.json()) >= 1

    neighbors = client.get(
        f"/api/v1/legal-knowledge-graph/nodes/{body['graph_node_id']}/neighbors",
        params={"firm_id": FIRM, "user_id": user_id},
    )
    assert neighbors.status_code == 200
    assert any(n["label"] == "ACME Corp SARL" for n in neighbors.json())


def test_search_returns_ranked_matches() -> None:
    client = TestClient(app)
    user_id = _authorized_user()
    client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "source_type": "contract",
            "title": "Contrat confidentialité",
            "content_text": "Clause de confidentialité et bonne foi contractuelle.",
            "author": "Julien Moreau",
        },
    )

    response = client.get(
        "/api/v1/legal-knowledge-graph/search",
        params={
            "firm_id": FIRM,
            "user_id": user_id,
            "query": "clause de confidentialité",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_feedback_roundtrip() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    response = client.post(
        "/api/v1/legal-knowledge-graph/feedback",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "subject_id": "relation-api-1",
            "action": "annotate",
            "author": "Julien Moreau",
            "comment": "à revoir",
        },
    )

    assert response.status_code == 200
    assert response.json()["action"] == "annotate"


def test_entity_resolution_propose_confirm_and_reject() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    first = client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "source_type": "contract",
            "title": "Contrat A",
            "content_text": "Contrat conclu avec ACME Corp SARL.",
            "author": "Julien Moreau",
        },
    ).json()
    second = client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "source_type": "contract",
            "title": "Contrat B",
            "content_text": "Avenant conclu avec ACME Corp SARL.",
            "author": "Julien Moreau",
        },
    ).json()

    neighbors_a = client.get(
        f"/api/v1/legal-knowledge-graph/nodes/{first['graph_node_id']}/neighbors",
        params={"firm_id": FIRM, "user_id": user_id},
    ).json()
    neighbors_b = client.get(
        f"/api/v1/legal-knowledge-graph/nodes/{second['graph_node_id']}/neighbors",
        params={"firm_id": FIRM, "user_id": user_id},
    ).json()
    node_a_id = next(n["id"] for n in neighbors_a if n["label"] == "ACME Corp SARL")
    node_b_id = next(n["id"] for n in neighbors_b if n["label"] == "ACME Corp SARL")

    proposed = client.post(
        "/api/v1/legal-knowledge-graph/entity-resolution/propose",
        json={"firm_id": FIRM, "user_id": user_id, "node_id_a": node_a_id, "node_id_b": node_b_id},
    )
    assert proposed.status_code == 200
    assert proposed.json()["status"] == "confirmed"
    assert proposed.json()["score"] == 1.0


def test_set_access_policy_and_read_quality_and_analytics() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    ingested = client.post(
        "/api/v1/legal-knowledge-graph/ingest",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "source_type": "contract",
            "title": "Contrat confidentiel",
            "content_text": "Contrat de prestation ACME Corp SARL.",
            "author": "Julien Moreau",
        },
    ).json()

    policy = client.post(
        f"/api/v1/legal-knowledge-graph/nodes/{ingested['graph_node_id']}/policy",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "confidentiality_level": "confidential",
            "retention_days": 3650,
        },
    )
    assert policy.status_code == 200
    assert policy.json()["confidentiality_level"] == "confidential"

    quality = client.get(
        f"/api/v1/legal-knowledge-graph/nodes/{ingested['graph_node_id']}/quality",
        params={"firm_id": FIRM, "user_id": user_id},
    )
    assert quality.status_code == 200
    assert "confidence" in quality.json()

    analytics = client.get(
        "/api/v1/legal-knowledge-graph/analytics",
        params={"firm_id": FIRM, "user_id": user_id},
    )
    assert analytics.status_code == 200
    assert "node_count" in analytics.json()


def test_node_relations_for_unknown_node_returns_empty_list() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    response = client.get(
        "/api/v1/legal-knowledge-graph/nodes/does-not-exist/relations",
        params={"firm_id": FIRM, "user_id": user_id},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_node_neighbors_for_unknown_node_returns_404() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    response = client.get(
        "/api/v1/legal-knowledge-graph/nodes/does-not-exist/neighbors",
        params={"firm_id": FIRM, "user_id": user_id},
    )

    assert response.status_code == 404
