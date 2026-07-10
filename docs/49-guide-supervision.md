# Guide Supervision (Sprint 10)

## Périmètre

Ce guide couvre `tmis.platform.logging`, `tmis.platform.observability`,
`tmis.platform.metrics`, `tmis.platform.health` et
`tmis.platform.monitoring`.

## Logs structurés

`core/logging.py` (structlog) intègre désormais
`RedactSensitiveFields` dans la chaîne de processeurs, **avant**
`JSONRenderer`. Toute clé de dictionnaire (au niveau racine ou imbriqué,
dans des `dict` ou des `list`) dont le nom (insensible à la casse)
figure dans l'ensemble configurable de clés sensibles (`password`,
`token`, `secret`, `api_key`...) est remplacée par `***REDACTED***` —
un `logger.info("login", password=raw)` ne fuite jamais un mot de passe
en clair dans les logs centralisés.

## Corrélation des requêtes

`trace_id_middleware` (Sprint 1, `core/observability.py`) pose
`request.state.trace_id` ; `correlation_middleware` (Sprint 10) le lie
aux contextvars de structlog (`bind_contextvars`/`clear_contextvars`)
pour que **chaque ligne de log émise pendant le traitement de la
requête**, à n'importe quelle profondeur d'appel, porte le même
`trace_id` sans avoir à le faire transiter explicitement par chaque
signature de fonction.

**Ordre critique** : `trace_id_middleware` doit s'exécuter avant
`correlation_middleware`. Dans Starlette, le dernier middleware ajouté
via `app.middleware("http")` est le premier exécuté — l'ordre d'ajout
dans `main.py` est donc l'inverse de l'ordre d'exécution logique,
documenté en commentaire à cet endroit précis.

## Métriques

`MetricsRegistry` (`platform/metrics/registry.py`) est un exposeur
Prometheus texte **hand-roulé, sans nouvelle dépendance** — même choix
que les writers PDF (Sprint 7) et XLSX (Sprint 9). Trois types :
`Counter` (cumulatif), `Gauge` (monte/descend), `Histogram` (buckets de
latence). `metrics_middleware` alimente `http_requests_total` et
`http_request_duration_seconds` sur chaque requête.

**Piège corrigé** : `Histogram.observe()` n'incrémente que le *premier*
bucket qualifiant (avec un `break`) — c'est `render()` qui effectue la
somme cumulative Prometheus standard. Incrémenter tous les buckets
qualifiants à l'observation *et* cumuler à nouveau au rendu aurait
compté chaque observation plusieurs fois. Couvert par un test de
non-régression explicite
(`test_histogram_bucket_counts_are_not_double_counted`).

## Health checks

`GET /platform/health/live` (jamais de sonde de dépendance — une panne
de base de données ne doit pas provoquer un redémarrage en cascade de
tous les pods) et `GET /platform/health/ready` (agrège les 7 sondes :
base de données, cache, stockage, AI Kernel, Event Bus, queue,
connecteurs ; `DOWN` > `DEGRADED` > `UP`, 503 si `DOWN`).

## Tableau de bord de supervision

`GET /platform/monitoring` compose l'état de santé, le compteur total
de requêtes et le coût IA cumulé en un instantané curaté — délibérément
distinct de `/platform/metrics` qui, lui, est exhaustif.

## Intégration future

Chaque module expose un port étroit (`HealthCheckPort`,
`CostSummaryPort`) pensé pour recevoir un exportateur réel
(Prometheus/Grafana, Datadog, OpenTelemetry) sans changement d'API —
voir le rapport de dette technique pour le détail de ce qui manque
encore.
