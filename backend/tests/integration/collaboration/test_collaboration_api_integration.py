import pytest
from fastapi.testclient import TestClient

from tmis.collaboration.bootstrap import (
    get_activity_feed,
    get_approval_store,
    get_audit_trail,
    get_collaboration_evaluator,
    get_collaboration_event_bus,
    get_comment_store,
    get_member_store,
    get_notification_engine,
    get_task_store,
    get_workspace_engine,
)
from tmis.main import app

_PREFIX = "/api/v1/collaboration"


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    get_workspace_engine.cache_clear()
    get_activity_feed.cache_clear()
    get_audit_trail.cache_clear()
    get_notification_engine.cache_clear()
    get_collaboration_event_bus.cache_clear()
    get_collaboration_evaluator.cache_clear()
    get_member_store.cache_clear()
    get_task_store.cache_clear()
    get_comment_store.cache_clear()
    get_approval_store.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_workspace(client: TestClient) -> dict:
    response = client.post(
        f"{_PREFIX}/workspaces",
        json={"firm_id": "firm-1", "name": "Cabinet Durand", "actor_id": "founder-1"},
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_get_workspace(client: TestClient) -> None:
    created = _create_workspace(client)

    response = client.get(f"{_PREFIX}/workspaces/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Cabinet Durand"


def test_get_unknown_workspace_returns_404(client: TestClient) -> None:
    response = client.get(f"{_PREFIX}/workspaces/does-not-exist")
    assert response.status_code == 404


def test_invite_member_and_change_status(client: TestClient) -> None:
    workspace = _create_workspace(client)

    invited = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/members",
        json={"email": "avocat@cabinet.fr", "display_name": "Jane Avocat", "actor_id": "founder-1"},
    )
    assert invited.status_code == 200
    member = invited.json()
    assert member["status"] == "invited"

    activated = client.post(
        f"{_PREFIX}/members/{member['id']}/status",
        json={"workspace_id": workspace["id"], "target": "active", "actor_id": "founder-1"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"


def test_change_status_with_an_illegal_transition_returns_400(client: TestClient) -> None:
    workspace = _create_workspace(client)
    invited = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/members",
        json={"email": "a@cabinet.fr", "display_name": "A", "actor_id": "founder-1"},
    ).json()

    response = client.post(
        f"{_PREFIX}/members/{invited['id']}/status",
        json={"workspace_id": workspace["id"], "target": "suspended", "actor_id": "founder-1"},
    )

    assert response.status_code == 400


def test_assign_role(client: TestClient) -> None:
    workspace = _create_workspace(client)
    member = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/members",
        json={"email": "a@cabinet.fr", "display_name": "A", "actor_id": "founder-1"},
    ).json()

    response = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/members/{member['id']}/role",
        json={"role": "associate", "actor_id": "founder-1"},
    )

    assert response.status_code == 204


def test_create_task_and_update_status(client: TestClient) -> None:
    workspace = _create_workspace(client)

    created = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/tasks",
        json={"title": "Rédiger la mise en demeure", "actor_id": "founder-1"},
    )
    assert created.status_code == 200
    task = created.json()
    assert task["status"] == "todo"

    fetched = client.get(f"{_PREFIX}/tasks/{task['id']}")
    assert fetched.status_code == 200

    updated = client.post(
        f"{_PREFIX}/tasks/{task['id']}/status",
        json={"workspace_id": workspace["id"], "target": "in_progress", "actor_id": "founder-1"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"


def test_update_task_status_illegal_transition_returns_400(client: TestClient) -> None:
    workspace = _create_workspace(client)
    task = client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/tasks",
        json={"title": "Task", "actor_id": "founder-1"},
    ).json()

    response = client.post(
        f"{_PREFIX}/tasks/{task['id']}/status",
        json={"workspace_id": workspace["id"], "target": "validated", "actor_id": "founder-1"},
    )

    assert response.status_code == 400


def test_get_unknown_task_returns_404(client: TestClient) -> None:
    response = client.get(f"{_PREFIX}/tasks/does-not-exist")
    assert response.status_code == 404


def test_add_and_list_comments(client: TestClient) -> None:
    workspace = _create_workspace(client)

    added = client.post(
        f"{_PREFIX}/comments",
        json={
            "workspace_id": workspace["id"],
            "target_type": "case",
            "target_id": "case-1",
            "author_id": "founder-1",
            "text": "Premier commentaire",
        },
    )
    assert added.status_code == 200

    listed = client.get(
        f"{_PREFIX}/comments", params={"target_type": "case", "target_id": "case-1"}
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_request_and_decide_approval(client: TestClient) -> None:
    workspace = _create_workspace(client)

    requested = client.post(
        f"{_PREFIX}/approvals",
        json={
            "workspace_id": workspace["id"],
            "target_type": "document",
            "target_id": "doc-1",
            "requested_by": "founder-1",
            "approver_ids": ["approver-1"],
            "mode": "single",
        },
    )
    assert requested.status_code == 200
    approval = requested.json()
    assert approval["status"] == "pending"

    decided = client.post(
        f"{_PREFIX}/approvals/{approval['id']}/decide",
        json={
            "workspace_id": workspace["id"],
            "approver_id": "approver-1",
            "decision": "approve",
            "actor_id": "approver-1",
        },
    )
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"

    fetched = client.get(f"{_PREFIX}/approvals/{approval['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "approved"


def test_decide_approval_by_a_non_approver_returns_400(client: TestClient) -> None:
    workspace = _create_workspace(client)
    approval = client.post(
        f"{_PREFIX}/approvals",
        json={
            "workspace_id": workspace["id"],
            "target_type": "document",
            "target_id": "doc-1",
            "requested_by": "founder-1",
            "approver_ids": ["approver-1"],
            "mode": "single",
        },
    ).json()

    response = client.post(
        f"{_PREFIX}/approvals/{approval['id']}/decide",
        json={
            "workspace_id": workspace["id"],
            "approver_id": "stranger",
            "decision": "approve",
            "actor_id": "stranger",
        },
    )

    assert response.status_code == 400


def test_mention_dispatches_a_notification_visible_through_the_api(client: TestClient) -> None:
    workspace = _create_workspace(client)

    client.post(
        f"{_PREFIX}/comments",
        json={
            "workspace_id": workspace["id"],
            "target_type": "case",
            "target_id": "case-1",
            "author_id": "founder-1",
            "text": "Pour avis @user:approver-1",
        },
    )

    response = client.get(f"{_PREFIX}/notifications/approver-1")

    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "mention"


def test_mark_notification_read(client: TestClient) -> None:
    workspace = _create_workspace(client)
    client.post(
        f"{_PREFIX}/comments",
        json={
            "workspace_id": workspace["id"],
            "target_type": "case",
            "target_id": "case-1",
            "author_id": "founder-1",
            "text": "@user:approver-1",
        },
    )
    notification = client.get(f"{_PREFIX}/notifications/approver-1").json()[0]

    response = client.post(f"{_PREFIX}/notifications/{notification['id']}/read")

    assert response.status_code == 200
    assert response.json()["read_at"] is not None


def test_activity_feed_lists_recorded_actions(client: TestClient) -> None:
    workspace = _create_workspace(client)
    client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/tasks",
        json={"title": "Task", "actor_id": "founder-1"},
    )

    response = client.get(f"{_PREFIX}/workspaces/{workspace['id']}/activity")

    assert response.status_code == 200
    activity_types = {entry["activity_type"] for entry in response.json()}
    assert "workspace" in activity_types
    assert "task" in activity_types


def test_activity_feed_can_be_filtered_by_activity_type(client: TestClient) -> None:
    workspace = _create_workspace(client)
    client.post(
        f"{_PREFIX}/workspaces/{workspace['id']}/tasks",
        json={"title": "Task", "actor_id": "founder-1"},
    )

    response = client.get(
        f"{_PREFIX}/workspaces/{workspace['id']}/activity", params={"activity_type": "task"}
    )

    assert response.status_code == 200
    entries = response.json()
    assert entries
    assert all(e["activity_type"] == "task" for e in entries)
