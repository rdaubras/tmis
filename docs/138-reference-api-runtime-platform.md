# Référence API — Cloud Native Runtime Platform (Sprint 23)

Base path : `/runtime` — **délibérément hors** de `/api/v1`, **non
authentifié**, monté directement sur `app` à côté de
`cloud_operations_router`/`platform_router`, même précédent déjà
établi : « préoccupation opérationnelle, pas une API métier
versionnée ».

| Méthode | Chemin | Description |
|---|---|---|
| POST | `/tasks` | Soumet une `RuntimeTask` (`?task_id=&name=&priority=&depends_on=&firm_id=`) |
| GET | `/tasks` | Liste toutes les tâches connues |
| GET | `/tasks/ready` | Tâches prêtes (dépendances résolues), triées par priorité |
| POST | `/tasks/{task_id}/cancel` | Annule une tâche (en attente ou en cours) |
| POST | `/jobs` | Place un job en file (`?queue_name=&priority=&max_attempts=&timeout_seconds=&delay_seconds=`) |
| POST | `/jobs/{job_id}/fail` | Marque un job en échec (`?error=`) — retry ou DLQ selon `max_attempts` |
| GET | `/jobs/dead-letters` | Jobs en Dead Letter Queue (`?queue_name=`) |
| GET | `/events/workflow/replay` | Rejoue les événements workflow depuis une séquence (`?from_sequence=`) |
| POST | `/events/workflow/archive` | Archive les événements avant une séquence (`?before_sequence=`) |
| GET | `/cache/stats` | Statistiques d'usage du cache distribué |
| POST | `/event-store/{stream_id}/events` | Journalise un événement (`?event_type=`, corps JSON = payload) |
| GET | `/event-store/{stream_id}/replay` | Rejoue un flux depuis le dernier snapshot |
| POST | `/event-store/{stream_id}/snapshot` | Enregistre un snapshot (corps JSON = état) |
| POST | `/event-store/{stream_id}/archive` | Archive un flux (bloque les futurs `append`) |
| POST | `/event-store/{stream_id}/restore` | Désarchive un flux |
| GET | `/optimizer/recommendations` | Recommandations d'optimisation (`?firm_id=`) |
| POST | `/ha/heartbeat/{node_id}` | Enregistre un battement de cœur |
| GET | `/ha/supervise` | Statut de tous les nœuds connus |
| GET | `/ha/failover/{node_id}` | Décision de failover pour un nœud |
| POST | `/disaster-recovery/policy/{firm_id}` | Définit la politique de sauvegarde (`?schedule_cron=&retention_days=`) |
| GET | `/disaster-recovery/simulate-restore/{backup_id}` | Simule une restauration (plan + intégrité) |
| GET | `/disaster-recovery/rpo-rto` | Estimation RPO/RTO (`?last_backup_at=`) |
| GET | `/autoscaling/recommend/{category}` | Recommandation de mise à l'échelle (`?current_replicas=&min_replicas=&max_replicas=...`) |
| GET | `/autoscaling/bottlenecks` | Goulets d'étranglement agrégés (`?limit=`) |
| POST | `/load-test/{preset}` | Lance une simulation de charge (`preset` = 100, 1000 ou 10000) |
| POST | `/chaos/{scenario}` | Déclenche un scénario de chaos (`?authorized=`) |
| POST | `/chaos/{scenario}/probe` | Sonde la disponibilité pendant un scénario actif |
| POST | `/chaos/{scenario}/recover` | Finalise la mesure de reprise (`?item_loss_count=`) |

`runtime_orchestrator.run`/`.resume` ne sont **volontairement pas
exposés** en REST — voir docs/133-guide-runtime-orchestrator.md.

## Codes d'erreur

- `404` : job/task introuvable pour une opération qui en requiert un.
- `409` : `POST /event-store/{stream_id}/events` sur un flux archivé ;
  `POST /chaos/{scenario}/recover` avant que la dépendance ait
  effectivement récupéré.
- `403` : `POST /chaos/{scenario}` en environnement `production` sans
  `authorized=true`.

## Voir aussi

docs/132-architecture-runtime-platform.md.
