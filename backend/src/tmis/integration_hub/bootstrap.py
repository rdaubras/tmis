from functools import lru_cache

from tmis.integration_hub.authentication.engine import AuthenticationEngine
from tmis.integration_hub.configuration.engine import ConfigurationEngine
from tmis.integration_hub.configuration.store import InMemoryConnectorConfigurationStore
from tmis.integration_hub.conflict_resolution.engine import ConflictResolutionEngine
from tmis.integration_hub.connector_framework.engine import ConnectorInvoker
from tmis.integration_hub.connector_registry.engine import ConnectorRegistryEngine
from tmis.integration_hub.connector_registry.store import InMemoryConnectorRegistryStore
from tmis.integration_hub.connectors.billing.connector import DemoBillingConnector
from tmis.integration_hub.connectors.calendar.connector import DemoCalendarConnector
from tmis.integration_hub.connectors.crm.connector import DemoCrmConnector
from tmis.integration_hub.connectors.dms.connector import DemoDmsConnector
from tmis.integration_hub.connectors.document_storage.connector import DemoDocumentStorageConnector
from tmis.integration_hub.connectors.esignature.connector import DemoESignatureConnector
from tmis.integration_hub.connectors.messaging.connector import DemoMessagingConnector
from tmis.integration_hub.developer_sdk.registration import register_connector
from tmis.integration_hub.event_bridge.bridge import EventBridge
from tmis.integration_hub.event_bridge.bus import IntegrationEventBus
from tmis.integration_hub.health.engine import register_connector_health_checks
from tmis.integration_hub.mapping.engine import MappingEngine
from tmis.integration_hub.mapping.store import InMemoryMappingProfileStore
from tmis.integration_hub.monitoring.engine import ConnectorMonitoringEngine
from tmis.integration_hub.monitoring.sinks import InMemoryConnectorMetricsSink
from tmis.integration_hub.queue.engine import InMemorySyncQueue
from tmis.integration_hub.retry.engine import IntegrationRetryPolicy
from tmis.integration_hub.sandbox.engine import ConnectorSandbox
from tmis.integration_hub.scheduler.engine import SyncSchedulerEngine
from tmis.integration_hub.scheduler.store import InMemorySyncSchedulerStore
from tmis.integration_hub.security.engine import IntegrationSecurityEngine, new_rotating_encryption
from tmis.integration_hub.synchronization.engine import SynchronizationEngine
from tmis.integration_hub.synchronization.store import InMemorySyncJobStore
from tmis.integration_hub.transformation.engine import TransformationEngine
from tmis.integration_hub.webhooks.engine import WebhookEngine
from tmis.integration_hub.webhooks.sender import LoggingWebhookSender
from tmis.integration_hub.webhooks.store import InMemoryWebhookSubscriptionStore
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.rate_limiting.limiter import InMemoryRateLimiter
from tmis.platform.security.secrets_rotation import InMemorySecretRotationStore
from tmis.workflow_automation.bootstrap import get_workflow_event_bus


@lru_cache
def get_integration_event_bus() -> IntegrationEventBus:
    """Process-wide composition root for `tmis.integration_hub` (see
    docs/97-architecture-integration-hub.md)."""
    return IntegrationEventBus()


@lru_cache
def get_event_bridge() -> EventBridge:
    return EventBridge(get_integration_event_bus(), get_workflow_event_bus())


@lru_cache
def get_connector_metrics_sink() -> InMemoryConnectorMetricsSink:
    return InMemoryConnectorMetricsSink()


@lru_cache
def get_connector_monitoring_engine() -> ConnectorMonitoringEngine:
    return ConnectorMonitoringEngine([get_connector_metrics_sink()])


@lru_cache
def get_connector_invoker() -> ConnectorInvoker:
    return ConnectorInvoker(get_connector_monitoring_engine())


@lru_cache
def get_connector_registry_engine() -> ConnectorRegistryEngine:
    engine = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    register_connector(
        engine,
        DemoMessagingConnector(),
        connector_id="messaging-demo",
        name="Messagerie (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoCalendarConnector(),
        connector_id="calendar-demo",
        name="Agenda (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoDocumentStorageConnector(),
        connector_id="document-storage-demo",
        name="Stockage documentaire (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoESignatureConnector(),
        connector_id="esignature-demo",
        name="Signature électronique (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoDmsConnector(),
        connector_id="dms-demo",
        name="GED (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoBillingConnector(),
        connector_id="billing-demo",
        name="Facturation (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    register_connector(
        engine,
        DemoCrmConnector(),
        connector_id="crm-demo",
        name="CRM (démo)",
        version="1.0.0",
        publisher="TMIS",
    )
    return engine


@lru_cache
def get_authentication_engine() -> AuthenticationEngine:
    return AuthenticationEngine()


@lru_cache
def get_integration_security_engine() -> IntegrationSecurityEngine:
    rotation = new_rotating_encryption(InMemorySecretRotationStore())
    return IntegrationSecurityEngine(rotation, InMemoryRateLimiter())


@lru_cache
def get_configuration_engine() -> ConfigurationEngine:
    return ConfigurationEngine(InMemoryConnectorConfigurationStore())


@lru_cache
def get_transformation_engine() -> TransformationEngine:
    return TransformationEngine()


@lru_cache
def get_mapping_profile_store() -> InMemoryMappingProfileStore:
    return InMemoryMappingProfileStore()


@lru_cache
def get_mapping_engine() -> MappingEngine:
    return MappingEngine(get_mapping_profile_store(), get_transformation_engine())


@lru_cache
def get_conflict_resolution_engine() -> ConflictResolutionEngine:
    return ConflictResolutionEngine()


@lru_cache
def get_synchronization_engine() -> SynchronizationEngine:
    return SynchronizationEngine(get_connector_invoker(), get_conflict_resolution_engine())


@lru_cache
def get_sync_job_store() -> InMemorySyncJobStore:
    return InMemorySyncJobStore()


@lru_cache
def get_sync_queue() -> InMemorySyncQueue:
    return InMemorySyncQueue()


@lru_cache
def get_sync_scheduler_engine() -> SyncSchedulerEngine:
    return SyncSchedulerEngine(InMemorySyncSchedulerStore())


@lru_cache
def get_integration_retry_policy() -> IntegrationRetryPolicy:
    return IntegrationRetryPolicy()


@lru_cache
def get_connector_sandbox() -> ConnectorSandbox:
    return ConnectorSandbox()


@lru_cache
def get_webhook_subscription_store() -> InMemoryWebhookSubscriptionStore:
    return InMemoryWebhookSubscriptionStore()


@lru_cache
def get_webhook_engine() -> WebhookEngine:
    get_event_bridge()  # ensures ExternalRecordChanged is bridged into workflow_automation
    return WebhookEngine(
        get_webhook_subscription_store(), LoggingWebhookSender(), get_integration_event_bus()
    )


@lru_cache
def get_health_check_engine() -> HealthCheckEngine:
    """Deliberately its own `HealthCheckEngine` instance, distinct
    from `tmis.platform.health.bootstrap.get_health_check_engine`
    (see docs/97-architecture-integration-hub.md) — the LIH registers
    one probe per connector, not per platform dependency."""
    engine = HealthCheckEngine()
    register_connector_health_checks(engine, get_connector_registry_engine())
    return engine
