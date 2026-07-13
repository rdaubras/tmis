# Guide — Supervision tenant et sécurité plateforme (Sprint 22)

## Supervision tenant

`tenant_monitoring.TenantMonitoringEngine.snapshot(firm_id)` compose
trois moteurs déjà existants sans en dupliquer aucun calcul :

- `business_platform.analytics.AnalyticsEngine` (Sprint 20) — MRR et
  coût IA total du cabinet.
- `business_platform.usage.UsageEngine` (Sprint 20) — utilisation de
  quotas (`quota_usage`).
- `cloud_operations.incident_management.IncidentManagementEngine`
  (Sprint 21) — nombre d'incidents ouverts pour ce cabinet.

```python
GET /cloud-operations/tenants/{firm_id}
```

**Comportement 404** : un cabinet sans abonnement
`business_platform.subscriptions` provoque une `KeyError` profonde
dans `AnalyticsEngine.build_dashboard` → `SubscriptionEngine.get`.
La route intercepte explicitement ce cas et retourne
`404 firm has no subscription` plutôt que de laisser remonter une
`500` non gérée — défaut réel découvert en testant directement
l'endpoint plutôt qu'en devinant le code de statut attendu, corrigé
dans ce même sprint.

**Absent délibérément** : la disponibilité par cabinet n'a pas de
concept SLA par tenant dans TMIS aujourd'hui (`sla.SLAEngine` du
Sprint 21 est scopé par `service_name`, pas par cabinet) — le schéma
`TenantMonitoringSnapshot` ne prétend donc pas exposer une
disponibilité, contrairement à ce qu'un lecteur pourrait attendre
d'un tableau de bord tenant complet.

## Supervision sécurité plateforme

`security_monitoring.SecurityMonitoringEngine.overview()` parcourt
l'historique de `identity_platform.security_events.SecurityEventBus`
(Sprint 19) et compte les événements par type
(`LoginSucceeded`, `LoginFailed`, etc.), toutes tenants confondus.

```python
GET /cloud-operations/security-monitoring
```

Ce module est délibérément **plateforme entière**, pas par cabinet —
`identity_platform.monitoring.IdentityMonitoringEngine.dashboard
(firm_id)` (Sprint 19) reste la vue de référence par cabinet ; les
deux sont complémentaires, jamais redondants.
