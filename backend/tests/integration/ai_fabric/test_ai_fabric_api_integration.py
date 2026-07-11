from fastapi.testclient import TestClient

from tmis.main import app


def test_list_models_returns_the_seeded_catalog() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-fabric/models")

    assert response.status_code == 200
    names = {m["name"] for m in response.json()}
    assert {"gpt-4-legal", "claude-legal", "local-ocr", "local-vision", "embed-small"} <= names


def test_get_unknown_model_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-fabric/models/unknown-model")

    assert response.status_code == 404


def test_route_endpoint_returns_an_explainable_decision() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/route",
        json={
            "firm_id": "firm-api-1",
            "task_type": "Rédaction",
            "prompt": "Rédige un avis sur ce bail.",
            "profile": "drafting",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model"]["profiles"]
    assert len(body["reasons"]) >= 2


def test_plan_endpoint_follows_the_default_pipeline() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/plan",
        json={"firm_id": "firm-api-1", "task_description": "Analyser le contrat de bail."},
    )

    assert response.status_code == 200
    steps = response.json()["steps"]
    assert [s["name"] for s in steps][:2] == ["Analyse documentaire", "Extraction"]
    assert steps[-1]["kind"] == "critique"
    assert steps[-1]["decision"] is None


def test_compare_endpoint_ranks_responses() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/compare",
        json={
            "prompt": "Le contrat est-il valide ?",
            "responses": {
                "gpt-x": "Le contrat est valide. Art. 1103 s'applique.",
                "claude-y": "Le contrat est valide.",
            },
        },
    )

    assert response.status_code == 200
    assert set(response.json()["ranked_model_names"]) == {"gpt-x", "claude-y"}


def test_critique_endpoint_flags_missing_citations() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/critique",
        json={"model_name": "gpt-x", "response_text": "Cela semble correct sans plus de détail."},
    )

    assert response.status_code == 200
    assert "aucune citation ou référence détectée" in response.json()["issues"]


def test_consensus_endpoint_preserves_divergences() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/consensus",
        json={
            "topic": "validité du contrat",
            "positions": [
                {
                    "model_name": "gpt-x",
                    "text": (
                        "Le contrat est valide. Art. 1103 du Code civil impose la force "
                        "obligatoire."
                    ),
                    "quality_score": 0.8,
                },
                {
                    "model_name": "claude-y",
                    "text": "Le contrat n'est pas valide. Aucune clause ne le rend opposable.",
                    "quality_score": 0.8,
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["divergences"]


def test_fuse_endpoint_preserves_provenance() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-fabric/fuse",
        json={
            "positions": [
                {"model_name": "gpt-x", "text": "Premier avis."},
                {"model_name": "claude-y", "text": "Second avis."},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provenance"] == {"segment-1": "gpt-x", "segment-2": "claude-y"}


def test_benchmark_endpoint_records_and_lists_runs() -> None:
    client = TestClient(app)

    run = client.post(
        "/api/v1/ai-fabric/benchmark",
        json={
            "model_name": "gpt-4-legal",
            "response_text": "Le contrat est valide. Art. 1103 s'applique.",
            "cost_usd": 0.02,
            "latency_ms": 900,
        },
    )
    assert run.status_code == 200

    history = client.get("/api/v1/ai-fabric/benchmark/gpt-4-legal")
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_telemetry_endpoint_returns_a_snapshot() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-fabric/telemetry", params={"firm_id": "firm-api-1"})

    assert response.status_code == 200
    assert len(response.json()["models"]) > 0


def test_costs_endpoint_returns_per_provider_breakdown() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai-fabric/costs", params={"firm_id": "firm-api-1"})

    assert response.status_code == 200
    assert "openai" in response.json()["cost_by_provider"]


def test_policy_lifecycle_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/ai-fabric/policies",
        json={
            "type": "country_restricted",
            "model_name": "gpt-4-legal",
            "reason": "hébergement UE uniquement",
            "allowed_countries": ["FR", "DE"],
        },
    )
    assert created.status_code == 200
    policy_id = created.json()["id"]

    evaluate_blocked = client.post(
        "/api/v1/ai-fabric/governance/evaluate",
        json={"firm_id": "firm-api-1", "model_name": "gpt-4-legal", "country": "US"},
    )
    assert evaluate_blocked.json()["allowed"] is False

    deactivated = client.post(f"/api/v1/ai-fabric/policies/{policy_id}/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False

    evaluate_allowed = client.post(
        "/api/v1/ai-fabric/governance/evaluate",
        json={"firm_id": "firm-api-1", "model_name": "gpt-4-legal", "country": "US"},
    )
    assert evaluate_allowed.json()["allowed"] is True

    history = client.get(
        "/api/v1/ai-fabric/governance/history",
        params={"firm_id": "firm-api-1", "model_name": "gpt-4-legal"},
    )
    assert len(history.json()) == 2


def test_deactivate_unknown_policy_returns_404() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/ai-fabric/policies/unknown-policy/deactivate")

    assert response.status_code == 404
