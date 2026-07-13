from tmis.cloud_operations.runbooks.schemas import Runbook, RunbookStep

DEFAULT_RUNBOOKS: tuple[Runbook, ...] = (
    Runbook(
        slug="ai-provider-unavailable",
        title="AI provider unavailable",
        trigger="AI Fabric health check reports a provider as DOWN",
        steps=[
            RunbookStep(1, "Check the provider's public status page for an ongoing outage."),
            RunbookStep(2, "Confirm ai_fabric.fallback.FallbackEngine is routing to a backup."),
            RunbookStep(3, "Verify ai_fabric.retry.RetryPolicy is not exhausting retries."),
            RunbookStep(4, "If no fallback exists, disable the capability via feature flags."),
            RunbookStep(5, "Notify affected firms and open an incident."),
        ],
        tags=["ai_fabric", "availability"],
    ),
    Runbook(
        slug="slow-database",
        title="Slow database",
        trigger="cloud_operations.performance snapshot shows elevated DATABASE latency",
        steps=[
            RunbookStep(1, "Check active connection count and long-running queries."),
            RunbookStep(2, "Use profiling.top_offenders(COSTLY_QUERY) to find the culprit."),
            RunbookStep(3, "Check platform.cache hit ratio to rule out a cache-miss storm."),
            RunbookStep(4, "Scale read replicas, or roll back a recent migration."),
        ],
        tags=["database", "performance"],
    ),
    Runbook(
        slug="platform-overload",
        title="Platform overload",
        trigger="cloud_operations.capacity forecast projects imminent SLO breach",
        steps=[
            RunbookStep(1, "Check cloud_operations.queue_monitoring for growing depth."),
            RunbookStep(2, "Scale the service per platform.deployment autoscaling policy."),
            RunbookStep(3, "Enable rate limiting or shed low-priority traffic if needed."),
        ],
        tags=["capacity", "performance"],
    ),
    Runbook(
        slug="sync-failure",
        title="Connector sync failure",
        trigger="Connector health check reports repeated sync failures",
        steps=[
            RunbookStep(1, "Check integration_hub.health.ConnectorHealthProbe for the connector."),
            RunbookStep(2, "Inspect integration_hub.queue retry counts for its sync queue."),
            RunbookStep(3, "Re-authenticate the connector if the failure is an auth error."),
            RunbookStep(4, "Pause the connector and notify the firm if it persists."),
        ],
        tags=["integration_hub", "connectors"],
    ),
    Runbook(
        slug="marketplace-incident",
        title="Marketplace incident",
        trigger="A published plugin or listing causes errors for installing firms",
        steps=[
            RunbookStep(1, "Unpublish or disable the listing via platform_sdk.marketplace."),
            RunbookStep(2, "Identify affected firms via marketplace_subscriptions."),
            RunbookStep(3, "Notify affected firms and open an incident by blast radius."),
        ],
        tags=["marketplace", "platform_sdk"],
    ),
)
