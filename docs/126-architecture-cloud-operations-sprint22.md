# Architecture — Cloud Operations, extensions Sprint 22

## Objectif et origine de ce sprint

Le prompt utilisateur pour ce sprint proposait une nouvelle
« Enterprise Observability & Reliability Platform » (EORP) à
`tmis.observability/`, avec ~22 modules. L'analyse préalable a montré
un recouvrement massif (~12-13 modules) avec `tmis.cloud_operations`,
livré au Sprint 21 : télémétrie, métriques, traçage, logs, health
checks, alertes, SLO/SLA, error tracking, incidents, dashboards,
capacité et diagnostics existaient déjà, sous des noms quasi
identiques et avec les mêmes responsabilités.

Plutôt que de dupliquer silencieusement ce socle (risque avéré de
deux sources de vérité concurrentes pour les mêmes concepts), la
question a été posée explicitement à l'utilisateur via
`AskUserQuestion`. Décision retenue : **traiter ce contenu comme le
Sprint 22, étendre `tmis.cloud_operations`** plutôt que créer un
second package. Ce sprint ne reconstruit donc aucun des modules déjà
livrés au Sprint 21 ; il ajoute uniquement les neuf domaines
authentiquement nouveaux introduits par le prompt : `audit_pipeline`,
`cost_monitoring`, `ai_monitoring`, `workflow_monitoring`,
`integration_monitoring`, `tenant_monitoring`, `security_monitoring`,
`retention`, `exports`.

## Les 9 nouveaux sous-modules

```
backend/src/tmis/cloud_operations/
├── audit_pipeline/       # timeline d'audit fusionnée (sécurité + IA + workflow)
├── cost_monitoring/      # snapshot de coût IA par modèle/utilisateur
├── ai_monitoring/        # historisation des scans hallucination/biais
├── workflow_monitoring/  # lecture agrégée de workflow_automation.metrics
├── integration_monitoring/  # lecture agrégée de integration_hub.monitoring
├── tenant_monitoring/     # vue tenant composée (business + incidents)
├── security_monitoring/    # vue plateforme des événements de sécurité
├── retention/                # politiques de rétention par catégorie de données d'observabilité
└── exports/                    # export CSV/JSON de métriques et incidents
```

Chaque module suit le même patron Clean Architecture déjà établi au
Sprint 21 : `schemas.py` → `ports.py` (si un point d'extension local
est nécessaire) → `store.py` (implémentation en mémoire, uniquement
quand le module gère un état propre) → `engine.py` → `__init__.py`.
Les modules purement compositionnels (`cost_monitoring`,
`workflow_monitoring`, `integration_monitoring`, `tenant_monitoring`,
`security_monitoring`) n'ont pas de `store.py` — ils ne font que lire
et agréger l'état d'autres moteurs déjà existants.

## Le principe directeur : composer, jamais reconstruire

| Ce sprint compose | Le moteur du sprint antérieur |
|---|---|
| `audit_pipeline.AuditPipelineEngine` | `identity_platform.audit.SecurityAuditEngine`, `ai_governance.audit.AIAuditEngine`, `workflow_automation.audit.WorkflowAuditEngine` (via leur `.list_for_firm(firm_id)` commun) |
| `cost_monitoring.CostMonitoringEngine` | `platform.cost_control.CostTrackerEngine` (Sprint 10) — aucune seconde comptabilité de coût |
| `ai_monitoring.AIMonitoringEngine` | `ai_governance.hallucination_detection.HallucinationDetectionEngine`, `ai_governance.bias_detection.BiasDetectionEngine` (Sprint 15) ; `.model_snapshot` délègue à `ai_fabric.telemetry.TelemetryDashboard` (Sprint 14) plutôt que de dupliquer son calcul |
| `workflow_monitoring.WorkflowMonitoringEngine` | `workflow_automation.metrics.WorkflowMetricsEngine` (Sprint 17) — sink confirmé sans appelant avant ce sprint |
| `integration_monitoring.IntegrationMonitoringEngine` | `integration_hub.monitoring.ConnectorMonitoringEngine` (Sprint 18) — sink confirmé sans appelant avant ce sprint |
| `tenant_monitoring.TenantMonitoringEngine` | `business_platform.analytics.AnalyticsEngine`, `business_platform.usage.UsageEngine` (Sprint 20), `cloud_operations.incident_management.IncidentManagementEngine` (Sprint 21) |
| `security_monitoring.SecurityMonitoringEngine` | `identity_platform.security_events.SecurityEventBus` (Sprint 19) — vue plateforme, complémentaire à `identity_platform.monitoring.IdentityMonitoringEngine.dashboard(firm_id)` qui reste la vue par cabinet |
| `exports.ObservabilityExportEngine` | `business_platform.exports.engine.ExportEngine.export_table` (Sprint 20), lui-même adossé à `cabinet_os.reports.exporters.CsvReportExporter` (Sprint 9) — aucune troisième implémentation de logique CSV/JSON |

Chaque composition est documentée dans la docstring du moteur
concerné. Le research préalable a confirmé par lecture directe du
code qu'aucun autre point de l'application n'appelait
`WorkflowMetricsEngine.record`/`.all()` ni
`ConnectorMonitoringEngine.record`/`.all()` — ces deux sinks du
Sprint 17/18 étaient une capacité livrée mais jamais branchée ; ce
sprint corrige ce point mort (voir
docs/131-guide-migration-cloud-operations-sprint22.md).

## Le patron « reader port »

`platform.cost_control`, `identity_platform.security_events` etc.
exposent des ports suffisamment larges pour être réutilisés tels
quels. Ce n'est pas le cas de `WorkflowMetricsSinkPort` et
`ConnectorMetricsSinkPort`, définis au Sprint 17/18 comme
strictement en écriture (`.record()` uniquement) — ils ne
promettaient aucune méthode de lecture. Plutôt qu'élargir ces ports
partagés (ce qui aurait forcé toute future implémentation alternative
à supporter la lecture même si elle n'en a pas besoin) ou utiliser un
`# type: ignore`, chaque module consommateur définit son propre port
de lecture local, restreint à la surface réellement exposée par
l'implémentation concrète en mémoire :

```python
class WorkflowMetricsReaderPort(Protocol):
    def all(self) -> list[WorkflowRunMetrics]: ...

class ConnectorMetricsReaderPort(Protocol):
    def all(self) -> list[ConnectorMetrics]: ...
    def for_connector(self, connector_id: str) -> list[ConnectorMetrics]: ...
    def success_rate(self, connector_id: str) -> float: ...
```

Ce patron (nommé ici pour la première fois « reader port ») est
proposé comme convention pour tout futur sprint consommant un sink
write-only existant sans vouloir en élargir le contrat public.

## Dualité audit/sécurité cabinet vs. plateforme

`audit_pipeline` fusionne trois pistes d'audit **scopées par
cabinet** (`.list_for_firm(firm_id)` uniforme sur les trois moteurs
sources). `collaboration.audit` et `platform.audit` (scopés par
espace de travail, sans `firm_id` direct) sont délibérément exclus de
cette fusion — un futur adaptateur serait nécessaire pour les
inclure, documenté ici comme limite connue plutôt que contournée
silencieusement.

À l'inverse, `security_monitoring` est conçu **plateforme entière**,
pas par cabinet — c'est un choix délibéré pour ne pas dupliquer
`identity_platform.monitoring.IdentityMonitoringEngine.dashboard
(firm_id)`, qui reste la vue de référence par cabinet.

## API REST — 14 nouveaux endpoints

Ajoutés au même routeur `/cloud-operations/*`, hors `/api/v1`, non
authentifié — voir docs/125-reference-api-cloud-operations.md pour la
liste complète et docs/127 à docs/130 pour le détail par domaine.

## Ce que ce sprint n'est pas

- Ce n'est **pas** une duplication du Sprint 21 : les 9 modules
  livrés ici sont entièrement nouveaux ; aucun fichier du Sprint 21
  n'est réécrit, seuls `bootstrap.py` et `api/routes.py` sont étendus.
- Ce n'est **pas** l'ancien Sprint « Module Document + Persistance »
  (renumérobé Sprint 23 par ce même sprint) : ce dernier concerne la
  gestion documentaire, sans rapport avec l'observabilité.
- Voir la note de révision dans docs/09-roadmap-30-sprints.md pour le
  détail du renumérotage (insertion nette, total 38 → 39 sprints).
