from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app


def test_template_instantiation_and_workflow_versioning_via_api() -> None:
    client = TestClient(app)

    templates = client.get("/api/v1/workflow-automation/templates")
    assert templates.status_code == 200
    assert len(templates.json()) == 6

    opening = next(t for t in templates.json() if t["case_type"] == "ouverture_dossier")
    instantiated = client.post(
        f"/api/v1/workflow-automation/templates/{opening['id']}/instantiate",
        json={"firm_id": "firm-api-wf", "owner": "avocat-1"},
    )
    assert instantiated.status_code == 200
    workflow = instantiated.json()
    assert workflow["version"] == 1
    assert workflow["status"] == "draft"

    activated = client.post(
        f"/api/v1/workflow-automation/workflows/{workflow['id']}/activate",
        json={"firm_id": "firm-api-wf"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    new_version = client.post(
        f"/api/v1/workflow-automation/workflows/{workflow['id']}/versions",
        json={"firm_id": "firm-api-wf", "owner": "avocat-1", "description": "v2"},
    )
    assert new_version.status_code == 200
    assert new_version.json()["version"] == 2

    versions = client.get(
        f"/api/v1/workflow-automation/workflows/key/{workflow['workflow_key']}/versions",
        params={"firm_id": "firm-api-wf"},
    )
    assert versions.status_code == 200
    assert len(versions.json()) == 2


def test_rule_creation_and_evaluation_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/workflow-automation/rules",
        json={
            "firm_id": "firm-api-rules",
            "name": "Gros dossier",
            "field": "amount",
            "comparator": "gt",
            "value": "10000",
        },
    )
    assert created.status_code == 200
    rule_id = created.json()["id"]

    evaluated_true = client.post(
        f"/api/v1/workflow-automation/rules/{rule_id}/evaluate",
        json={"firm_id": "firm-api-rules", "context": {"amount": "20000"}},
    )
    assert evaluated_true.status_code == 200
    assert evaluated_true.json() is True

    evaluated_false = client.post(
        f"/api/v1/workflow-automation/rules/{rule_id}/evaluate",
        json={"firm_id": "firm-api-rules", "context": {"amount": "500"}},
    )
    assert evaluated_false.json() is False


def test_simulation_never_touches_real_data_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/workflow-automation/workflows",
        json={
            "firm_id": "firm-api-sim",
            "name": "Test simulation",
            "owner": "avocat-1",
            "steps": [
                {"order": 0, "name": "step-1", "action_type": "create_task", "action_config": {}}
            ],
        },
    )
    assert created.status_code == 200
    workflow_id = created.json()["id"]

    simulated = client.post(
        "/api/v1/workflow-automation/simulate",
        json={"firm_id": "firm-api-sim", "workflow_id": workflow_id, "context": {}},
    )
    assert simulated.status_code == 200
    body = simulated.json()
    assert body["would_complete"] is True
    assert body["steps"][0]["would_run"] is True


def test_approval_gateway_workflow_via_api() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/workflow-automation/approvals/configure",
        json={"firm_id": "firm-api-approval", "action_type": "generate_draft", "required": True},
    )
    required = client.get(
        "/api/v1/workflow-automation/approvals/requires",
        params={"firm_id": "firm-api-approval", "action_type": "generate_draft"},
    )
    assert required.json() == {"required": True}

    requested = client.post(
        "/api/v1/workflow-automation/approvals/request",
        json={
            "firm_id": "firm-api-approval",
            "action_id": "action-1",
            "requested_by": "avocat-1",
            "approver_ids": ["associe-1"],
        },
    )
    assert requested.status_code == 200
    request_id = requested.json()["id"]

    get_role_engine().assign("firm-api-approval", "associe-1", Role.PARTNER)
    decided = client.post(
        f"/api/v1/workflow-automation/approvals/{request_id}/decide",
        json={"firm_id": "firm-api-approval", "approver_id": "associe-1", "decision": "approve"},
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"


def test_audit_export_via_api() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/workflow-automation/audit/export", params={"firm_id": "firm-audit-1"}
    )
    assert response.status_code == 200
    assert response.text.startswith("id,workflow_id")
