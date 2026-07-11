from fastapi.testclient import TestClient

from tmis.main import app


def test_chain_step_lifecycle_via_api() -> None:
    client = TestClient(app)

    step = client.post(
        "/api/v1/ai-governance/chain/steps",
        params={"firm_id": "firm-api-1", "production_id": "prod-chain-1"},
        json={"stage": "question", "summary": "Le bail est-il résiliable ?"},
    )
    assert step.status_code == 200
    assert step.json()["stage"] == "question"

    client.post(
        "/api/v1/ai-governance/chain/steps",
        params={"firm_id": "firm-api-1", "production_id": "prod-chain-1"},
        json={"stage": "brouillon", "summary": "Brouillon rédigé."},
    )

    chain = client.get(
        "/api/v1/ai-governance/chain/prod-chain-1", params={"firm_id": "firm-api-1"}
    )
    assert chain.status_code == 200
    assert len(chain.json()["steps"]) == 2

    graph = client.get(
        "/api/v1/ai-governance/chain/prod-chain-1/graph", params={"firm_id": "firm-api-1"}
    )
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) == 2
    assert len(graph.json()["edges"]) == 1


def test_decision_record_lifecycle_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/ai-governance/decisions",
        json={
            "firm_id": "firm-api-1",
            "production_id": "prod-dec-1",
            "context": "Analyse du bail",
            "objective": "Déterminer la résiliation",
            "decision": "Résiliation possible",
            "justification": "Clause résolutoire expresse activée",
        },
    )
    assert created.status_code == 200

    history = client.get(
        "/api/v1/ai-governance/decisions/prod-dec-1", params={"firm_id": "firm-api-1"}
    )
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_confidence_and_risk_endpoints() -> None:
    client = TestClient(app)

    confidence = client.post(
        "/api/v1/ai-governance/confidence",
        json={
            "production_id": "prod-conf-1",
            "source_quality": 0.8,
            "reasoning_coherence": 0.9,
            "human_validation": 0.0,
            "multi_agent_consensus": 0.7,
            "model_stability": 0.85,
        },
    )
    assert confidence.status_code == 200
    assert 0.0 <= confidence.json()["value"] <= 1.0

    risks = client.post(
        "/api/v1/ai-governance/risks",
        json={
            "citation_count": 0,
            "contradiction_count": 0,
            "confidence_value": 0.9,
            "human_validated": False,
        },
    )
    assert risks.status_code == 200
    categories = [r["category"] for r in risks.json()]
    assert "missing_sources" in categories
    assert "no_human_validation" in categories


def test_explainability_and_provenance_endpoints() -> None:
    client = TestClient(app)

    explanation = client.post(
        "/api/v1/ai-governance/explanations",
        json={
            "firm_id": "firm-api-1",
            "production_id": "prod-expl-1",
            "summary": "Le bail peut être résilié.",
            "steps_followed": ["Question", "Analyse"],
            "legal_references": ["Code civil art. 1103"],
        },
    )
    assert explanation.status_code == 200

    history = client.get(
        "/api/v1/ai-governance/explanations/prod-expl-1", params={"firm_id": "firm-api-1"}
    )
    assert len(history.json()) == 1

    provenance = client.post(
        "/api/v1/ai-governance/provenance",
        json={
            "firm_id": "firm-api-1",
            "production_id": "prod-expl-1",
            "granularity": "paragraph",
            "locator": "para-1",
            "excerpt": "Art. 1103",
            "source_type": "statute_article",
            "source_reference": "Code civil art. 1103",
        },
    )
    assert provenance.status_code == 200

    trace = client.get(
        "/api/v1/ai-governance/provenance/prod-expl-1", params={"firm_id": "firm-api-1"}
    )
    assert len(trace.json()) == 1


def test_bias_hallucination_and_ethics_scan_endpoints() -> None:
    client = TestClient(app)

    bias = client.post(
        "/api/v1/ai-governance/bias-scan",
        json={"text": "Les hommes sont plus doués pour la négociation directe."},
    )
    assert bias.status_code == 200
    assert len(bias.json()) == 1

    hallucination = client.post(
        "/api/v1/ai-governance/hallucination-scan",
        json={"text": "Cela semble correct sans plus de précision."},
    )
    assert hallucination.status_code == 200
    assert len(hallucination.json()) == 1

    ethics = client.post(
        "/api/v1/ai-governance/ethics-scan",
        json={"text": "Il est garanti que vous gagnerez ce procès."},
    )
    assert ethics.status_code == 200
    assert len(ethics.json()) == 1


def test_policy_lifecycle_and_evaluation_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/ai-governance/policies",
        json={
            "firm_id": "firm-api-policy",
            "type": "min_confidence_threshold",
            "reason": "seuil minimal cabinet",
            "min_confidence": 0.7,
        },
    )
    assert created.status_code == 200
    policy_id = created.json()["id"]

    blocked = client.post(
        "/api/v1/ai-governance/policies/evaluate",
        json={
            "firm_id": "firm-api-policy",
            "production_id": "prod-policy-1",
            "confidence_value": 0.5,
        },
    )
    assert blocked.json()["allowed"] is False

    client.post(f"/api/v1/ai-governance/policies/{policy_id}/deactivate")

    allowed = client.post(
        "/api/v1/ai-governance/policies/evaluate",
        json={
            "firm_id": "firm-api-policy",
            "production_id": "prod-policy-1",
            "confidence_value": 0.5,
        },
    )
    assert allowed.json()["allowed"] is True


def test_human_validation_hierarchical_flow_via_api() -> None:
    client = TestClient(app)

    request = client.post(
        "/api/v1/ai-governance/validations/hierarchical",
        json={
            "firm_id": "firm-api-1",
            "production_id": "prod-val-1",
            "requested_by": "user-1",
            "approver_tiers": [["associate-1"], ["partner-1"]],
        },
    )
    assert request.status_code == 200
    request_id = request.json()["id"]
    assert request.json()["status"] == "pending"

    tier_one = client.post(
        f"/api/v1/ai-governance/validations/{request_id}/decide",
        json={"firm_id": "firm-api-1", "approver_id": "associate-1", "decision": "approve"},
    )
    assert tier_one.json()["status"] == "pending"

    tier_two = client.post(
        f"/api/v1/ai-governance/validations/{request_id}/decide",
        json={"firm_id": "firm-api-1", "approver_id": "partner-1", "decision": "approve"},
    )
    assert tier_two.json()["status"] == "approved"

    history = client.get(
        "/api/v1/ai-governance/validations/prod-val-1", params={"firm_id": "firm-api-1"}
    )
    assert len(history.json()) == 1


def test_decide_on_unknown_validation_request_returns_404() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-governance/validations/unknown-id/decide",
        json={"firm_id": "firm-api-1", "approver_id": "approver-1", "decision": "approve"},
    )

    assert response.status_code == 404


def test_audit_record_list_and_export_via_api() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/ai-governance/audit",
        json={
            "firm_id": "firm-api-audit",
            "production_id": "prod-audit-1",
            "actor_id": "user-1",
            "action": "draft_generated",
            "model_name": "gpt-4-legal",
        },
    )

    listed = client.get("/api/v1/ai-governance/audit", params={"firm_id": "firm-api-audit"})
    assert len(listed.json()) == 1

    exported = client.get(
        "/api/v1/ai-governance/audit/export", params={"firm_id": "firm-api-audit"}
    )
    assert exported.status_code == 200
    assert "model_name" in exported.text


def test_compliance_check_via_api() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-governance/compliance/check",
        json={
            "firm_id": "firm-api-compliance",
            "production_id": "prod-compliance-1",
            "confidence_value": 0.2,
            "citation_count": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert body["blocking_reasons"]


def test_quality_endpoint() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai-governance/quality",
        json={
            "production_id": "prod-quality-1",
            "explainability_completeness": 1.0,
            "provenance_completeness": 1.0,
            "confidence_value": 1.0,
            "risk_absence": 1.0,
            "human_validation_coverage": 1.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["overall"] == 1.0


def test_overview_endpoint_aggregates_every_engine() -> None:
    client = TestClient(app)
    firm_id, production_id = "firm-api-overview", "prod-overview-1"

    client.post(
        "/api/v1/ai-governance/chain/steps",
        params={"firm_id": firm_id, "production_id": production_id},
        json={"stage": "question", "summary": "Question posée."},
    )
    client.post(
        "/api/v1/ai-governance/decisions",
        json={
            "firm_id": firm_id,
            "production_id": production_id,
            "context": "c",
            "objective": "o",
            "decision": "d",
            "justification": "j",
        },
    )

    overview = client.get(
        f"/api/v1/ai-governance/overview/{production_id}", params={"firm_id": firm_id}
    )

    assert overview.status_code == 200
    body = overview.json()
    assert len(body["reasoning_chain"]["steps"]) == 1
    assert len(body["decisions"]) == 1
