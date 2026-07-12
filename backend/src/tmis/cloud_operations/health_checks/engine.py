from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.identity_platform.authorization.engine import AuthorizationEngine
from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine


def register_business_context_health_checks(
    engine: HealthCheckEngine,
    *,
    model_registry: ModelRegistryPort,
    plugin_registry: InMemoryPluginRegistry,
    workflow_engine: WorkflowEngine,
    authorization_engine: AuthorizationEngine,
    subscription_engine: SubscriptionEngine,
) -> None:
    """Registers the five components the sprint names that `platform.
    health.bootstrap` (Sprint 10) does not already probe — API and
    database are already covered there, Integration Hub is already
    covered per-connector by `integration_hub.health.
    register_connector_health_checks` (Sprint 18). Composes
    `platform.health.HealthCheckEngine`/`CallableHealthCheck`
    directly, the same pattern Sprint 18 established, rather than
    building a second health-aggregation engine. Every probe here is
    a lightweight, synchronous, structural check — same documented
    limitation as the seven checks already registered in `platform.
    health.bootstrap` (constructed and reachable, not a real
    round-trip probe)."""
    engine.register(CallableHealthCheck("ai_fabric", lambda: len(model_registry.list_all()) > 0))
    engine.register(CallableHealthCheck("marketplace", lambda: plugin_registry is not None))
    engine.register(CallableHealthCheck("workflow_engine", lambda: workflow_engine is not None))
    engine.register(
        CallableHealthCheck("identity_platform", lambda: authorization_engine is not None)
    )
    engine.register(
        CallableHealthCheck("business_platform", lambda: subscription_engine is not None)
    )
