"""DoD item 1: an unauthenticated request to any protected route is
impossible — every bounded context under `protected_router`
(`tmis.api.v1.router`) is sampled at least once, plus the public
allowlist proving those routes still work with no token at all."""

import pytest
from fastapi.testclient import TestClient

_PROTECTED_SAMPLE = [
    ("GET", "/api/v1/cases"),
    ("GET", "/api/v1/cases/00000000-0000-0000-0000-000000000000"),
    ("GET", "/api/v1/cases/case-1/profile"),
    ("POST", "/api/v1/chat/stream"),
    ("GET", "/api/v1/documents/doc-1"),
    ("POST", "/api/v1/watches"),
    ("GET", "/api/v1/legal-research/history"),
    ("GET", "/api/v1/legal-reasoning/sessions/session-1"),
    ("GET", "/api/v1/legal-drafting/drafts/doc-1"),
    ("GET", "/api/v1/collaboration/workspaces/workspace-1"),
    ("GET", "/api/v1/cabinet-os/clients"),
    ("GET", "/api/v1/ai-team/agents"),
    ("GET", "/api/v1/cabinet-knowledge/objects"),
    ("GET", "/api/v1/platform-sdk/marketplace"),
    ("GET", "/api/v1/ai-fabric/models"),
    ("GET", "/api/v1/ai-governance/chain/production-1"),
    ("GET", "/api/v1/strategic-intelligence/hypotheses/case-1"),
    ("GET", "/api/v1/workflow-automation/workflows/workflow-1"),
    ("GET", "/api/v1/integration-hub/connectors"),
    ("GET", "/api/v1/identity-platform/departments"),
    ("GET", "/api/v1/business-platform/plans"),
    ("GET", "/api/v1/legal-copilots"),
    ("GET", "/api/v1/legal-knowledge-graph/search"),
]

_PUBLIC_SAMPLE = [
    ("GET", "/"),
    ("GET", "/api/v1/health"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
]


@pytest.mark.parametrize("method, path", _PROTECTED_SAMPLE)
def test_protected_route_rejects_missing_token(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, path)
    assert response.status_code == 401, f"{method} {path} -> {response.status_code}"


@pytest.mark.parametrize("method, path", _PROTECTED_SAMPLE)
def test_protected_route_rejects_garbage_token(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, path, headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401, f"{method} {path} -> {response.status_code}"


@pytest.mark.parametrize("method, path", _PUBLIC_SAMPLE)
def test_public_allowlist_route_needs_no_token(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, path)
    assert response.status_code != 401, f"{method} {path} -> {response.status_code}"


def test_login_and_refresh_are_public() -> None:
    from tmis.api.v1.router import public_router

    paths = {route.path for route in public_router.routes}  # type: ignore[attr-defined]
    assert "/auth/login" in paths
    assert "/auth/refresh" in paths
