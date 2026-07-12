# Rapport d'architecture — Sprint 23 (Cloud Native Runtime Platform)

## Résumé

Le Sprint 23 ajoute `backend/src/tmis/runtime_platform/` (12
sous-modules, 30+ endpoints REST). Le prompt utilisateur exigeait une
Phase 1 d'audit exhaustif avant toute implémentation ; cet audit
(reproduit dans docs/132-architecture-runtime-platform.md) a
directement déterminé la portée : composer l'existant partout où
c'était possible, construire du neuf seulement là où un vide réel
était confirmé.

Points de contact hors `runtime_platform/` :

- `tmis/main.py` — branchement du nouveau routeur REST
  (`runtime_platform_router`), monté directement sur `app`, hors
  `/api/v1`, à côté de `cloud_operations_router`.
- `tmis/legal_research/bootstrap.py` — `get_research_orchestrator()`
  construit désormais `ResearchCache(DistributedCacheEngine(kernel.cache))`
  au lieu de `ResearchCache(kernel.cache)` — migration réelle, zéro
  changement d'API publique.
- `tmis/cloud_operations/chaos_testing/engine.py` — la garde de
  sécurité production (`if environment == "production" and not
  authorized: raise ...`) a été extraite en une fonction top-level
  `ensure_chaos_authorized`, réutilisée telle quelle par
  `runtime_platform.chaos_engineering.RuntimeChaosEngine` — extension,
  pas duplication de la règle de sécurité.
- `tmis/runtime_platform/runtime_orchestrator/adapters.py` — nouveau
  fichier, mais lit `workflow_automation.execution_engine.
  ExecutionEngine`/`.schemas` sans modifier ce module.

## Conformité aux principes architecturaux

- **Phase 1 obligatoire avant code** : contrairement aux sprints
  précédents où la recherche de réutilisation était une étape interne
  au processus de livraison, ce sprint l'exigeait explicitement comme
  livrable de sa propre spécification — traité comme tel, avec un
  agent de recherche dédié dont les résultats sont reproduits dans
  docs/132.
- **Composer, ne jamais reconstruire** : huit compositions explicites
  documentées dans docs/132, vers des moteurs des Sprints 2, 10, 17,
  21, 22. Aucun module de télémétrie/métriques/traçage/alertes/
  incidents (Sprint 21) ni de supervision transverse (Sprint 22)
  n'est reconstruit.
- **Le patron « decorate, don't replace »** (nouveau ce sprint, voir
  docs/134) : `EventStreamingEngine` type sa dépendance contre un
  `Protocol` de deux méthodes (`publish`/`history`) que les sept bus
  existants partagent déjà structurellement, plutôt que de forcer un
  choix parmi eux ou de les remplacer.
- **Event Driven Architecture** : `EventEnvelope`, `StoredEvent`,
  `RuntimeChaosResult` sont tous immuables ou append-only, cohérent
  avec le reste de la base événementielle de TMIS.
- **Sécurité — chaos engineering jamais en production sans
  autorisation** : `ensure_chaos_authorized` est désormais un point
  de contrôle unique partagé par `cloud_operations.chaos_testing` et
  `runtime_platform.chaos_engineering` — vérifié par
  `tests/unit/runtime_platform/test_chaos_engineering.py::
  test_production_requires_explicit_authorization`.
- **Simulation honnête, pas de fausse infrastructure** :
  `load_testing.LoadTestingEngine` et `chaos_engineering.
  RuntimeChaosEngine` documentent explicitement qu'ils simulent
  (utilisateurs virtuels in-process, circuit forcé ouvert) plutôt que
  de provoquer une vraie disruption réseau — même compromis de
  transparence que le Sprint 21.

## Rapport de migration/extension par composant cité par le sprint

| Composant cible | État avant ce sprint | Action de ce sprint |
|---|---|---|
| `ai.cache.CachePort`/`RedisCache` | Cache distribué réel, sans invalidation applicative, warming, compression ni statistiques | Décoré par `DistributedCacheEngine` ; `legal_research` migré en exemple représentatif |
| 7 bus d'événements existants | Aucun replay/idempotence/versionnage/archivage | Décorables par `EventStreamingEngine` sans modification ; `workflow_automation.event_bus` décoré en démonstration dans `bootstrap.py` |
| `platform.disaster_recovery.DisasterRecoveryEngine` | Décision de failover à seuil unique, pas de suivi par nœud | Étendu par `HighAvailabilityEngine` (heartbeat, statut, supervision multi-nœuds) |
| `platform.backup`/`platform.restore` | Sauvegarde/restauration réelles, sans politique ni simulation combinée | Composés par `RuntimeDisasterRecoveryEngine` (politiques, simulation, RPO/RTO) |
| `cloud_operations.chaos_testing.ChaosTestingEngine` | 4 scénarios, garde de sécurité non réutilisable | Garde extraite (`ensure_chaos_authorized`) ; 3 scénarios supplémentaires + mesure automatique via `RuntimeChaosEngine` |
| `workflow_automation.execution_engine.ExecutionEngine` | Aucun lien avec un ordonnanceur inter-domaines | Réutilisé (jamais modifié) via l'adaptateur `workflow_execution_task_runner` |

## Dette technique identifiée

- `cqrs.CommandBus`/`QueryBus` sont des fondations sans adoption :
  aucun domaine métier n'y est migré par ce sprint (délibéré,
  conforme au prompt : « l'adoption sera progressive »).
- `event_store.EventStoreEngine` n'est branché sur aucun flux métier
  réel — fondation disponible, pas une migration d'un domaine
  existant vers l'Event Sourcing.
- `RuntimeDisasterRecoveryEngine.estimate_rpo_rto` dépend d'un
  `last_backup_at` fourni par l'appelant ; aucun domaine n'agrège
  encore automatiquement la date de dernière sauvegarde par cabinet.
- `runtime_orchestrator.run`/`.resume` ne sont pas exposés en REST
  (limite architecturale documentée dans docs/133, pas un oubli).

## Vérification finale

```
$ .venv/bin/ruff check src tests
All checks passed!

$ .venv/bin/mypy src
Success: no issues found in 1738 source files

$ .venv/bin/pytest -q
1825 passed, 4 skipped, 2 warnings in 11.21s
```

1825 tests passent (1754 hérités des Sprints 1-22, 71 nouveaux dédiés
au Sprint 23 : 60 unitaires couvrant les 12 sous-modules par grappes
fonctionnelles, 11 d'intégration couvrant les 30+ endpoints REST).
