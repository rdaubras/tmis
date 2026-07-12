# Guide — Audit pipeline, coût IA et qualité IA (Sprint 22)

## Pipeline d'audit fusionné

`audit_pipeline.AuditPipelineEngine.timeline(firm_id)` fusionne trois
pistes d'audit déjà tenues par des sprints antérieurs, chacune
scopée par cabinet :

- `identity_platform.audit.SecurityAuditEngine` (connexions,
  changements de permission, événements de sécurité)
- `ai_governance.audit.AIAuditEngine` (générations IA, décisions de
  gouvernance)
- `workflow_automation.audit.WorkflowAuditEngine` (démarrage/
  complétion/annulation de workflows)

Chaque source expose `.list_for_firm(firm_id)`, mappé vers un
`AuditPipelineEvent` uniforme (`source`, `action`, `summary`,
`occurred_at`) puis trié chronologiquement. Aucune donnée n'est
recopiée en base : `timeline()` interroge les trois moteurs à chaque
appel, donc reflète toujours leur état courant.

```python
GET /cloud-operations/audit/{firm_id}
```

## Supervision de coût IA

`cost_monitoring.CostMonitoringEngine.snapshot(firm_id)` regroupe les
entrées de `platform.cost_control.CostTrackerEngine` (Sprint 10) par
modèle et par utilisateur, et rapporte le nombre de seuils
d'alerte franchis (`cost_tracker.check_thresholds(firm_id)`) ainsi
que le taux de cache (`cost_tracker.cache_hit_rate(firm_id)`).
Aucune nouvelle comptabilité de coût n'est introduite — ce module ne
fait que présenter une vue agrégée de données déjà collectées.

```python
GET /cloud-operations/cost/{firm_id}
```

## Supervision qualité IA

`ai_monitoring.AIMonitoringEngine` historise ce qui, avant ce sprint,
était strictement éphémère : les résultats de
`ai_governance.hallucination_detection.HallucinationDetectionEngine`
et `ai_governance.bias_detection.BiasDetectionEngine` (Sprint 15)
n'étaient retournés qu'à l'appelant d'un seul appel, jamais
conservés. `scan_and_record(text, firm_id=None)` exécute les deux
scans, enregistre chaque anomalie détectée dans un
`InMemoryAIQualityIncidentStore` local et incrémente une métrique
`MetricCategory.ERRORS` nommée `ai_quality.{kind}` sur
`cloud_operations.metrics.MetricsEngine` — cohérent avec le reste des
métriques Sprint 21.

`.model_snapshot(firm_id)` ne duplique pas
`dashboards.ai_dashboard` : il délègue directement à
`ai_fabric.telemetry.TelemetryDashboard(firm_id).snapshot()`
(Sprint 14), qui reste l'unique source de vérité pour le coût/
latence/qualité/repli par modèle.

```python
POST /cloud-operations/ai-quality/{firm_id}/scan?text=...
GET  /cloud-operations/ai-quality/incidents/recent?limit=50
GET  /cloud-operations/ai-quality/{firm_id}
```

## Limite connue

`audit_pipeline` n'inclut pas `collaboration.audit` ni
`platform.audit`, scopés par espace de travail plutôt que par
`firm_id` — un adaptateur de mapping espace de travail → cabinet
serait nécessaire pour les intégrer ; non fait dans ce sprint pour
éviter une hypothèse de correspondance non vérifiée.
