# Démo — Sprint 23 (Cloud Native Runtime Platform)

Démonstration exécutée via `TestClient(app)` (`/runtime/...`) et les
singletons `runtime_platform.bootstrap` — sortie capturée telle
quelle.

## 1. Runtime Orchestrator — dépendances et priorité (Python, pas REST)

```
ready avant complétion: ['demo-ingest']
statut ingest: done
ready après complétion: ['demo-notify']
```

`demo-notify` dépend de `demo-ingest` : il n'apparaît dans
`ready_tasks()` qu'une fois `demo-ingest` marqué `DONE` — la
résolution de dépendances fonctionne. `run()`/`resume()` ne sont pas
exposés en REST (voir docs/133) ; cette étape appelle directement
l'API Python, comme le ferait un caller réel.

## 2. Async Processing — Dead Letter Queue via l'API

```
job après échec immédiat: dead_lettered
DLQ: ['job-f3d2f61f5f0f']
```

Un job soumis avec `max_attempts=0` passe directement en
`DEAD_LETTERED` au premier échec — `GET /runtime/jobs/dead-letters`
le retrouve.

## 3. Event Streaming — décore le bus workflow existant

```
événements avant: 0
```

`GET /runtime/events/workflow/replay` interroge
`EventStreamingEngine` construit sur le singleton
`workflow_automation.event_bus.WorkflowEventBus` — `0` ici car aucun
workflow n'a publié d'événement dans ce processus de démonstration ;
`tests/unit/runtime_platform/test_event_streaming.py` démontre le
replay/idempotence/archivage sur un bus peuplé.

## 4. Distributed Cache — décore `ai.cache.CachePort`

```
cache stats: {'hits': 1, 'misses': 1, 'sets': 1, 'invalidations': 0,
              'warmed_keys': 0, 'bytes_saved_by_compression': 0}
```

Un `set` puis un `get` réussi (`hits=1`) et un `get` sur une clé
absente (`misses=1`) — `GET /runtime/cache/stats` lit le même
singleton `DistributedCacheEngine` que celui manipulé directement ici
en Python.

## 5. Event Store — journalisation, snapshot, replay

```
replay depuis le dernier snapshot: ['PlanChanged']
```

`SubscriptionActivated` est journalisé, puis un snapshot est pris,
puis `PlanChanged` est journalisé — `replay()` ne retourne que les
événements postérieurs au snapshot, la démonstration de l'Event
Sourcing générique.

## 6. Runtime Optimizer — recommandations

```
nombre de recommandations: 0
```

Aucune métrique CPU/mémoire/latence n'a été enregistrée dans ce
processus de démonstration, donc aucun seuil n'est dépassé — `0`
recommandations est le résultat honnête, cohérent avec
`tests/unit/runtime_platform/test_runtime_optimizer.py`, qui démontre
des recommandations réelles sur des métriques dépassant les seuils.

## 7. High Availability — heartbeat, supervision, failover

```
supervision: {'node-demo-1': 'healthy'}
failover: {'should_failover': False, 'reason': 'heartbeat within threshold'}
```

Un battement de cœur récent classe le nœud `HEALTHY` ; la décision de
failover, déléguée à `platform.disaster_recovery.
DisasterRecoveryEngine`, refuse à juste titre puisque le battement
est dans les temps.

## 8. Disaster Recovery — politique et estimation RPO/RTO

```
politique: {'firm_id': 'firm-demo', 'schedule_cron': '0 3 * * *', 'retention_days': 90}
RPO/RTO sans sauvegarde connue: {'rto_minutes': 60, 'rpo_minutes': 15,
                                  'actual_rpo_minutes': None, 'meets_objective': False}
```

Sans `last_backup_at` connu, l'objectif ne peut pas être considéré
comme atteint — comportement honnête plutôt qu'un optimisme non
fondé.

## 9. Load Testing — 1 000 utilisateurs virtuels simulés

```
concurrent_users=1000 throughput_rps=145874 p95_latency_ms=0.00
```

1 000 tâches `asyncio` concurrentes contre une cible interne
triviale — démontre le harnais de simulation ; un caller réel
substitue sa propre coroutine cible pour mesurer un vrai chemin
métier.

## 10. Chaos Engineering — cycle complet run → probe → recover

```
scénario déclenché: {'scenario': 'message_bus_loss', 'dependency': 'runtime_platform.event_bus'}
disponible pendant la panne: False
reprise mesurée: {'scenario': 'message_bus_loss', 'recovery_time_seconds': 0.01155,
                   'availability_ratio': 0.0, 'item_loss_count': 3}
```

Le scénario `MESSAGE_BUS_LOSS` force le circuit
`runtime_platform.event_bus` ouvert ; une sonde pendant la panne
confirme l'indisponibilité (`availability_ratio=0.0`, un seul appel
de sonde) ; après simulation de la reprise
(`CircuitBreaker.record_success`), `measure_recovery` calcule le
temps de reprise réel et accepte le nombre de pertes fourni par
l'appelant (`item_loss_count=3`) — la mesure automatique que le
Sprint 21 ne calculait pas.
