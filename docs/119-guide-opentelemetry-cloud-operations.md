# Guide — Télémétrie façon OpenTelemetry (Sprint 21)

## Pourquoi une façade et non une dépendance OpenTelemetry

TMIS n'a aujourd'hui aucune dépendance à un SDK OpenTelemetry, à
`prometheus-client`, ni à un exportateur de traces — choix délibéré,
cohérent avec le reste du socle observability (`platform.metrics`,
`platform.monitoring`, Sprint 10), qui est hand-rolled pour éviter
d'ajouter une dépendance lourde pour un scope encore mono-processus.
`tmis.cloud_operations.telemetry.TelemetryEngine` reproduit la forme
de l'API OpenTelemetry — `record_metric`, `start_span`, `end_span`,
`emit_event` — sans en dépendre, afin de rester « indépendant des
outils de supervision » (contrainte explicite du sprint) tout en
gardant la même forme d'appel qu'un futur SDK réel.

```python
from tmis.cloud_operations.bootstrap import get_telemetry_engine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.tracing.schemas import SpanKind

telemetry = get_telemetry_engine()

span = telemetry.start_span("trace-abc", SpanKind.AI_FABRIC, "route-model")
telemetry.record_metric(MetricCategory.AI_CALL_DURATION, "gpt-4o", 340.0, firm_id="firm-1")
telemetry.end_span(span.id)
telemetry.emit_event("model.selected", firm_id="firm-1", payload={"model": "gpt-4o"})
```

## Ce qui est déjà réel derrière la façade

- `record_metric` écrit dans `cloud_operations.metrics.MetricsEngine`,
  qui écrit lui-même dans `platform.metrics.MetricsRegistry`
  (Sprint 10) — visible immédiatement sur `GET /platform/metrics`
  (format d'exposition Prometheus).
- `start_span`/`end_span` écrivent dans `cloud_operations.tracing.
  TracingEngine`, dont le `trace_id` est toujours celui déjà posé
  par `core.observability.trace_id_middleware` (Sprint 1) sur
  `request.state.trace_id` — jamais un second schéma de
  corrélation.
- `emit_event` historise dans un store en mémoire, interrogeable via
  `events_for_firm`.

## Migrer vers un vrai SDK OpenTelemetry plus tard

Le jour où TMIS a besoin d'exporter vers un vrai collecteur (Jaeger,
Tempo, Datadog, etc.), seul `TelemetryEngine` change d'implémentation
interne — sa signature publique (`record_metric`/`start_span`/
`end_span`/`emit_event`) ne change pas, donc aucun appelant
(`workflow_automation.execution_engine`, `ai_fabric.router`,
`platform.observability.middleware`) n'a besoin d'être modifié. C'est
exactement le rôle d'une façade : isoler le choix d'outil de
supervision du reste du code métier, contrainte explicite du sprint
(« rester compatible avec plusieurs solutions de supervision »).
