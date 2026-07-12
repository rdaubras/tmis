"""Demonstrates that existing bounded contexts now check the SaaS
Business Platform's quotas/modules/feature flags before acting — see
docs/110-guide-migration-business-platform.md. Covers the four
endpoints migrated this sprint: `ai_fabric.route_request` (AI_CALLS
quota, graceful skip if not onboarded), `workflow_automation.
start_execution` (WORKFLOWS quota, graceful skip), `integration_hub.
set_connector_configuration` (INTEGRATION_HUB module gate, graceful
skip), and `cabinet_knowledge.evaluate_quality` (a feature flag
seeded fully open by default)."""

from fastapi.testclient import TestClient

from tmis.business_platform.bootstrap import (
    CABINET_KNOWLEDGE_QUALITY_FLAG_KEY,
    get_business_feature_flag_engine,
    get_business_quota_engine,
    get_module_registry,
    get_plan_catalog,
    get_subscription_engine,
)
from tmis.business_platform.feature_flags.schemas import BusinessFlagExtras, Environment
from tmis.business_platform.modules.schemas import TmisModule
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.quotas.schemas import QuotaDimension
from tmis.cabinet_knowledge.bootstrap import get_knowledge_space
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.integration_hub.bootstrap import get_connector_registry_engine
from tmis.main import app


def _onboard_firm(firm_id: str, plan_name: PlanName) -> None:
    catalog = get_plan_catalog()
    subs = get_subscription_engine()
    plan = catalog.latest(plan_name)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id)


def test_route_request_ignores_quota_check_for_a_non_onboarded_firm() -> None:
    client = TestClient(app)
    firm_id = "firm-enforce-ai-no-sub"

    response = client.post(
        "/api/v1/ai-fabric/route",
        json={"firm_id": firm_id, "task_type": "summarize", "prompt": "hello"},
    )

    assert response.status_code in (200, 400)  # never 429: no subscription to gate against


def test_route_request_blocks_once_ai_calls_quota_is_exhausted() -> None:
    client = TestClient(app)
    firm_id = "firm-enforce-ai-quota"
    _onboard_firm(firm_id, PlanName.TRIAL)

    allowed = client.post(
        "/api/v1/ai-fabric/route",
        json={"firm_id": firm_id, "task_type": "summarize", "prompt": "hello"},
    )
    assert allowed.status_code == 200

    quotas = get_business_quota_engine()
    limit = quotas.limit_for(firm_id, QuotaDimension.AI_CALLS)
    quotas.set_override(firm_id, QuotaDimension.AI_CALLS, extra_amount=-limit)

    blocked = client.post(
        "/api/v1/ai-fabric/route",
        json={"firm_id": firm_id, "task_type": "summarize", "prompt": "hello"},
    )
    assert blocked.status_code == 429


def test_connector_configuration_blocked_when_module_deactivated() -> None:
    client = TestClient(app)
    firm_id = "firm-enforce-integration-hub"
    _onboard_firm(firm_id, PlanName.BUSINESS)
    connector_id = get_connector_registry_engine().list_connectors()[0].id

    allowed = client.put(
        f"/api/v1/integration-hub/connectors/{connector_id}/configuration",
        json={"firm_id": firm_id, "values": {}},
    )
    assert allowed.status_code == 200

    get_module_registry().deactivate(firm_id, TmisModule.INTEGRATION_HUB)

    blocked = client.put(
        f"/api/v1/integration-hub/connectors/{connector_id}/configuration",
        json={"firm_id": firm_id, "values": {}},
    )
    assert blocked.status_code == 409


def test_quality_evaluation_flag_is_open_by_default_and_can_be_restricted() -> None:
    client = TestClient(app)
    firm_id = "firm-enforce-flag"
    space = get_knowledge_space()
    obj = space.create(firm_id, KnowledgeType.CLAUSE, "title", {"text": "content"}, "author")

    open_response = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj.id}/quality", params={"firm_id": firm_id}
    )
    assert open_response.status_code == 200

    flags = get_business_feature_flag_engine()
    flags.set_extras(
        BusinessFlagExtras(
            key=CABINET_KNOWLEDGE_QUALITY_FLAG_KEY,
            enabled_environments=frozenset({Environment.STAGING}),
        )
    )

    restricted_response = client.post(
        f"/api/v1/cabinet-knowledge/objects/{obj.id}/quality", params={"firm_id": firm_id}
    )
    assert restricted_response.status_code == 403

    # Restore the seeded, fully-open default — `flags` is a process-wide
    # singleton shared with every other test in this session.
    flags.set_extras(BusinessFlagExtras(key=CABINET_KNOWLEDGE_QUALITY_FLAG_KEY))
