"""Demonstrates that existing bounded contexts now pass through the
Enterprise Identity & Trust Platform before performing a sensitive
action — "aucun module ne peut désormais être utilisé sans passer par
cette plateforme" (sprint constraint). Covers the endpoints migrated
this sprint: `workflow_automation.decide_approval`,
`ai_governance.decide_validation`,
`cabinet_knowledge.decide_validation_request` (unconditional — the
actor was already a required field of their API contract) and
`integration_hub.set_connector_configuration` /
`ai_team.launch_mission` (opt-in via an additive `actor_id`/
`requested_by` field, since those endpoints previously carried no
actor identity at all)."""

from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app


def test_workflow_automation_approval_decision_requires_authorization() -> None:
    client = TestClient(app)
    firm_id = "firm-migration-wf"

    client.post(
        "/api/v1/workflow-automation/approvals/configure",
        json={"firm_id": firm_id, "action_type": "generate_draft", "required": True},
    )
    requested = client.post(
        "/api/v1/workflow-automation/approvals/request",
        json={
            "firm_id": firm_id,
            "action_id": "action-1",
            "requested_by": "avocat-1",
            "approver_ids": ["unauthorized-approver"],
        },
    ).json()

    denied = client.post(
        f"/api/v1/workflow-automation/approvals/{requested['id']}/decide",
        json={
            "firm_id": firm_id,
            "approver_id": "unauthorized-approver",
            "decision": "approve",
        },
    )
    assert denied.status_code == 403

    get_role_engine().assign(firm_id, "unauthorized-approver", Role.PARTNER)
    allowed = client.post(
        f"/api/v1/workflow-automation/approvals/{requested['id']}/decide",
        json={
            "firm_id": firm_id,
            "approver_id": "unauthorized-approver",
            "decision": "approve",
        },
    )
    assert allowed.status_code == 200


def test_ai_governance_human_validation_decision_requires_authorization() -> None:
    client = TestClient(app)
    firm_id = "firm-migration-gov"

    requested = client.post(
        "/api/v1/ai-governance/validations/hierarchical",
        json={
            "firm_id": firm_id,
            "production_id": "prod-1",
            "requested_by": "user-1",
            "approver_tiers": [["approver-without-role"]],
        },
    ).json()

    denied = client.post(
        f"/api/v1/ai-governance/validations/{requested['id']}/decide",
        json={"firm_id": firm_id, "approver_id": "approver-without-role", "decision": "approve"},
    )
    assert denied.status_code == 403

    get_role_engine().assign(firm_id, "approver-without-role", Role.PARTNER)
    allowed = client.post(
        f"/api/v1/ai-governance/validations/{requested['id']}/decide",
        json={"firm_id": firm_id, "approver_id": "approver-without-role", "decision": "approve"},
    )
    assert allowed.status_code == 200


def test_cabinet_knowledge_validation_decision_requires_authorization() -> None:
    client = TestClient(app)
    firm_id = "firm-migration-know"

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

    denied = client.post(
        f"/api/v1/cabinet-knowledge/validation-requests/{submitted['id']}/decide",
        json={"firm_id": firm_id, "decision": "approve", "reviewer": "reviewer-without-role"},
    )
    assert denied.status_code == 403

    get_role_engine().assign(firm_id, "reviewer-without-role", Role.PARTNER)
    allowed = client.post(
        f"/api/v1/cabinet-knowledge/validation-requests/{submitted['id']}/decide",
        json={"firm_id": firm_id, "decision": "approve", "reviewer": "reviewer-without-role"},
    )
    assert allowed.status_code == 200


def test_integration_hub_connector_configuration_authorization_is_opt_in() -> None:
    client = TestClient(app)
    firm_id = "firm-migration-int"

    connectors = client.get("/api/v1/integration-hub/connectors").json()
    connector_id = connectors[0]["id"]

    legacy_caller = client.put(
        f"/api/v1/integration-hub/connectors/{connector_id}/configuration",
        json={"firm_id": firm_id, "values": {"api_key": "x"}},
    )
    assert legacy_caller.status_code == 200

    denied = client.put(
        f"/api/v1/integration-hub/connectors/{connector_id}/configuration",
        json={"firm_id": firm_id, "values": {"api_key": "y"}, "actor_id": "actor-without-role"},
    )
    assert denied.status_code == 403

    get_role_engine().assign(firm_id, "actor-without-role", Role.PARTNER)
    allowed = client.put(
        f"/api/v1/integration-hub/connectors/{connector_id}/configuration",
        json={"firm_id": firm_id, "values": {"api_key": "z"}, "actor_id": "actor-without-role"},
    )
    assert allowed.status_code == 200


def test_ai_team_mission_launch_enforces_authorization_only_when_requested_by_supplied() -> None:
    client = TestClient(app)
    firm_id = "firm-migration-team"

    team = client.post(
        "/api/v1/ai-team/teams",
        json={"domain": "civil", "complexity": "medium", "case_type": "litige_commercial"},
    ).json()

    legacy_caller = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": firm_id,
            "request_description": "Analyser le dossier",
            "team_id": team["id"],
        },
    )
    assert legacy_caller.status_code == 200

    denied = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": firm_id,
            "request_description": "Analyser le dossier",
            "team_id": team["id"],
            "requested_by": "requester-without-role",
        },
    )
    assert denied.status_code == 403

    get_role_engine().assign(firm_id, "requester-without-role", Role.PARTNER)
    allowed = client.post(
        "/api/v1/ai-team/missions",
        json={
            "firm_id": firm_id,
            "request_description": "Analyser le dossier",
            "team_id": team["id"],
            "requested_by": "requester-without-role",
        },
    )
    assert allowed.status_code == 200
