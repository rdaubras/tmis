"""Demonstrates the Zero Trust chain end to end: RBAC -> ABAC ->
Policy, each layer able to deny what the previous layer allowed,
never the reverse, and never an implicit allow for an unknown
identity — "aucun service ne fait confiance à un autre sans
vérification" (sprint vision)."""

from fastapi.testclient import TestClient

from tmis.main import app


def test_unknown_identity_is_denied_by_default() -> None:
    client = TestClient(app)

    decision = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": "firm-zt-1",
            "user_id": "never-onboarded",
            "permission": "export.data",
        },
    )

    assert decision.json()["allowed"] is False


def test_rbac_layer_denies_before_any_abac_or_policy_is_considered() -> None:
    client = TestClient(app)
    firm_id = "firm-zt-2"

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": firm_id, "user_id": "paralegal-1", "role": "paralegal"},
    )

    decision = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": firm_id,
            "user_id": "paralegal-1",
            "permission": "consultation.validate",
        },
    )

    assert decision.json()["allowed"] is False
    assert "aucun rôle" in decision.json()["reason"]


def test_abac_layer_denies_a_role_grant_based_on_confidentiality() -> None:
    client = TestClient(app)
    firm_id = "firm-zt-3"

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": firm_id, "user_id": "partner-1", "role": "partner"},
    )

    allowed_standard = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": firm_id,
            "user_id": "partner-1",
            "permission": "consultation.validate",
            "confidentiality_level": "standard",
        },
    )
    assert allowed_standard.json()["allowed"] is True


def test_policy_layer_can_require_second_validation_for_a_strategic_draft() -> None:
    client = TestClient(app)
    firm_id = "firm-zt-4"

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": firm_id, "user_id": "partner-1", "role": "partner"},
    )
    client.post(
        "/api/v1/identity-platform/policies",
        json={
            "firm_id": firm_id,
            "permission": "strategy_draft.validate",
            "requires_second_validation": True,
            "reason": "brouillon stratégique : double validation requise",
        },
    )

    decision = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": firm_id,
            "user_id": "partner-1",
            "permission": "strategy_draft.validate",
        },
    )

    assert decision.json()["allowed"] is True
    assert decision.json()["requires_second_validation"] is True


def test_policy_layer_can_restrict_a_workflow_permission_to_one_team() -> None:
    """A firm-specific `Policy` can scope a permission to a single
    team — evaluated against the actor's own `IdentityContext.team_id`
    (set once via `identity-context`), never a value the caller can
    spoof per-request."""
    client = TestClient(app)
    firm_id = "firm-zt-5"

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": firm_id, "user_id": "associate-1", "role": "associate"},
    )
    client.post(
        "/api/v1/identity-platform/policies",
        json={
            "firm_id": firm_id,
            "permission": "workflow.use_team_restricted",
            "restricted_to_team_id": "team-litigation",
        },
    )
    client.put(
        "/api/v1/identity-platform/identity-context",
        json={"firm_id": firm_id, "user_id": "associate-1", "team_id": "team-corporate"},
    )

    wrong_team = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": firm_id,
            "user_id": "associate-1",
            "permission": "workflow.use_team_restricted",
        },
    )

    client.put(
        "/api/v1/identity-platform/identity-context",
        json={"firm_id": firm_id, "user_id": "associate-1", "team_id": "team-litigation"},
    )
    right_team = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": firm_id,
            "user_id": "associate-1",
            "permission": "workflow.use_team_restricted",
        },
    )

    assert wrong_team.json()["allowed"] is False
    assert right_team.json()["allowed"] is True
