# Guide — Dashboards (Sprint 21)

## Les six vues

`cloud_operations.dashboards.DashboardsEngine` expose six vues, dont
quatre sont une pure composition de moteurs déjà construits (aucune
nouvelle source de vérité) :

| Vue | Endpoint | Source |
|---|---|---|
| Plateforme | `GET /cloud-operations/dashboards/overview` (`platform_status`) | `platform.monitoring.MonitoringEngine` (Sprint 10) |
| Workflows | inclus dans `overview` (`workflows_executed`) | `cloud_operations.metrics` (nouveau) |
| Intégrations | inclus dans `overview` (`integrations_healthy`/`integrations_total`) | `integration_hub.connector_registry`/`.health` (Sprint 18, nouveau) |
| IA (par cabinet) | `ai_dashboard(firm_id)` | `ai_fabric.telemetry.TelemetryDashboard` (Sprint 14) |
| Sécurité (par cabinet) | `security_dashboard(firm_id)` | `identity_platform.monitoring.IdentityMonitoringEngine` (Sprint 19) |
| Business (par cabinet) | `business_dashboard(firm_id)` | `business_platform.analytics.AnalyticsEngine` (Sprint 20) |

## Vue globale vs vue par cabinet

`overview(firm_id=None)` retourne une vue plateforme-globale où
`ai`/`security`/`business` restent `None` — ces trois dashboards n'ont
pas de signification cross-cabinet (un score de risque IA ou un
chiffre d'affaires « tous cabinets confondus mélangés » serait
trompeur). Passer un `firm_id` explicite peuple les trois.

```python
from tmis.cloud_operations.bootstrap import get_dashboards_engine

dashboards = get_dashboards_engine()
platform_view = dashboards.overview()               # ai/security/business = None
firm_view = dashboards.overview(firm_id="firm-123")  # les trois peuplés
```

## Workflows et intégrations — les deux vues authentiquement nouvelles

`WorkflowsDashboard` (total de workflows exécutés, total d'erreurs)
est construit à partir de l'historique `cloud_operations.metrics`
(catégories `WORKFLOW_COUNT`/`ERRORS`), alimenté par l'instrumentation
de `workflow_automation.execution_engine` (voir
docs/124-guide-migration-cloud-operations.md). `IntegrationsDashboard`
interroge `integration_hub.connector_registry.list_connectors()` et
sonde chaque connecteur avec `integration_hub.health.
ConnectorHealthProbe` — aucune donnée dupliquée, juste agrégée.
