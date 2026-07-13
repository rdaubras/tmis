# Guide — Rétention et exports d'observabilité (Sprint 22)

## Politiques de rétention

`retention.RetentionEngine` gère une politique par
`ObservabilityDataCategory` (`METRICS`, `TRACES`, `AUDIT_EVENTS`,
`INCIDENTS`), avec des valeurs par défaut réalistes plutôt
qu'arbitraires :

| Catégorie | Rétention par défaut |
|---|---|
| `METRICS` | 90 jours |
| `TRACES` | 30 jours |
| `AUDIT_EVENTS` | 2 555 jours (≈ 7 ans, standard légal courant) |
| `INCIDENTS` | 365 jours |

```python
GET  /cloud-operations/retention/{category}
POST /cloud-operations/retention/{category}?retention_days=...
```

`is_expired(category, occurred_at)` permet à tout module appelant de
décider s'il doit purger un enregistrement — ce sprint expose la
politique et le calcul d'expiration, il n'exécute **aucune purge
automatique** : la suppression effective d'anciennes données reste un
travail futur, documenté ici comme portée volontairement limitée.

## Exports

`exports.ObservabilityExportEngine` ne réimplémente aucune logique
CSV/JSON. Il construit un `cabinet_os.reports.schemas.ReportTable` à
partir des `MetricEvent`/`Incident` demandés et délègue entièrement à
`business_platform.exports.engine.ExportEngine.export_table`
(Sprint 20) — qui lui-même s'appuie sur
`cabinet_os.reports.exporters.CsvReportExporter` (Sprint 9) pour le
CSV et construit le JSON directement. C'est la troisième couche de
cette chaîne de réutilisation ; aucune n'est dupliquée.

```python
GET /cloud-operations/exports/incidents?export_format=csv|json&firm_id=...
GET /cloud-operations/exports/metrics/{category}?export_format=csv|json
```

Le module n'a pas de `schemas.py` propre : il réutilise directement
`ExportFormat` et `ExportResult` de
`business_platform.exports.schemas`, cohérent avec le principe de ne
jamais définir un second schéma pour un concept déjà modélisé
ailleurs.
