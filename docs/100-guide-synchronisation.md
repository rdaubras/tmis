# Guide — Synchronisation (Sprint 18)

## Configurer un job

```python
from tmis.integration_hub.synchronization import SyncDirection, SyncJobConfig, SyncMode
from tmis.integration_hub.conflict_resolution import ConflictStrategy

job = SyncJobConfig(
    id="sync-1", connector_id="crm-demo", firm_id="firm-1", entity_type="client",
    direction=SyncDirection.PULL, mode=SyncMode.INCREMENTAL,
    conflict_strategy=ConflictStrategy.REMOTE_WINS,
)
```

`direction` (`PULL`/`PUSH`/`BIDIRECTIONAL`) et `mode` (`FULL`/
`INCREMENTAL`) sont indépendants ; `INCREMENTAL` transmet
`job.last_synced_at` en cursor `since` au connecteur, `FULL` transmet
`None`.

## Exécuter un job : `SynchronizationEngine.run_pull`

```python
report = await sync_engine.run_pull(
    job, connector, config_values,
    mapper=ConnectorMapper(mapping_engine, connector_id=job.connector_id, firm_id=job.firm_id),
    local_lookup=my_local_lookup,  # optionnel — voir ci-dessous
)
```

`run_pull` :

1. lit via `ConnectorInvoker.safe_read` (journalisé, voir
   `docs/98-guide-framework-connecteurs.md`) ;
2. mappe chaque enregistrement (`mapper`, optionnel — sans lui, le
   mapping est identité) ;
3. si `local_lookup` est fourni et trouve un enregistrement local
   différent, déclenche `conflict_resolution` selon
   `job.conflict_strategy` ;
4. retourne un `SyncRunReport` (`records_read`, `records_written`,
   `conflicts`, `conflicts_pending_validation`).

`MapperPort` et `LocalRecordLookupPort` sont des entrées découplées :
la synchronisation ne dépend jamais directement de `mapping` ni d'un
contexte métier propriétaire des données locales (`cabinet_knowledge`,
`case_intelligence`...) — l'appelant les fournit.

## Mapper les champs : `mapping`

Un `MappingProfile` par (connecteur, cabinet, type d'entité) définit
la correspondance champ source → champ cible, avec une transformation
optionnelle :

```python
from tmis.integration_hub.mapping import FieldMapping, MappingProfile

store.save(MappingProfile(
    id="mp-1", connector_id="crm-demo", firm_id="firm-1", entity_type="client",
    fields=(
        FieldMapping(source_field="Nom", target_field="name", transform_id="uppercase"),
        FieldMapping(source_field="DateCreation", target_field="created_at", transform_id="date_iso"),
    ),
))
```

`transformation.TransformationEngine` fournit `uppercase`,
`lowercase`, `trim`, `date_iso` par défaut ; `engine.register()` ajoute
une transformation sans toucher au moteur.

## Résoudre un conflit : `conflict_resolution`

Quatre stratégies, sélectionnables par job :

| Stratégie | Comportement |
|---|---|
| `LOCAL_WINS` | l'enregistrement local est conservé |
| `REMOTE_WINS` | l'enregistrement distant écrase le local |
| `LAST_WRITE_WINS` | compare `updated_at`, garde le plus récent |
| `HUMAN_VALIDATION` | soumet une demande à `ai_governance.human_validation`, retourne `pending_human_validation=True` tant qu'aucune décision n'a été prise |

`HumanValidationStrategy` ne réimplémente rien : elle compose
`HumanValidationEngine` (Sprint 15) déjà utilisé par
`strategic_intelligence.review` et
`workflow_automation.approval_gateway`.

## File et planification : `queue` et `scheduler`

`InMemorySyncQueue` ordonne les jobs par priorité (comme
`ai_team.work_queue`, réimplémenté localement) avec
`enqueue`/`dequeue_next`/`mark_running`/`mark_done`/`mark_failed`/
`check_timeouts`. `SyncSchedulerEngine.schedule(firm_id, job_id,
next_fire_at, interval)` puis `due(firm_id, now)` pilotent la
planification horaire (pas de boucle de fond dans ce sprint — un futur
processus planificateur appelle `due()` périodiquement).

`retry.IntegrationRetryPolicy.run(operation)` applique un backoff
exponentiel autour d'un appel asynchrone qui échoue transitoirement.
