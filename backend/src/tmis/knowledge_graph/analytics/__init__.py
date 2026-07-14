"""Knowledge graph federation metrics — composes
`tmis.cloud_operations.metrics.MetricsEngine` (Sprint 21) for
historized storage rather than building a parallel metrics store.
`MetricCategory` is extended additively with `GRAPH_COVERAGE`,
`ENTITY_RESOLUTION_RATE`, and `SEMANTIC_LINK_DENSITY` — same convention
as the Sprint 24 Legal Copilot Framework extension.
"""
