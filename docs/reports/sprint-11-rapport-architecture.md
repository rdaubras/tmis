# Rapport d'architecture — Sprint 11 (AI Team Platform)

## Résumé

Le Sprint 11 ajoute `backend/src/tmis/ai_team/` (18 sous-modules + une
couche API) au-dessus du `TMISKernel` (Sprint 2) et du système
d'agents Sprint 1 (`tmis.ai.schemas.agent.AgentPort`/`AgentInput`/
`AgentOutput`, réutilisés tels quels). Aucun module métier des Sprints
2-10 n'a été modifié ; seuls `tmis/api/v1/router.py` (branchement du
routeur) et rien d'autre ont été touchés hors `ai_team/`.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque module suit le même
  patron que les sprints précédents — `schemas.py` → `ports.py` →
  implémentation(s) → `bootstrap.py`. Aucune exception sur les 18
  modules.
- **Event Driven Architecture** : bien que ce sprint n'introduise pas
  encore de bus d'événements dédié à `ai_team` (les événements
  `EventBus` du Kernel restent le seul mécanisme d'événements existant
  et ne sont pas nécessaires à l'orchestration synchrone d'une
  mission), les points d'extension (délégation, changement de statut
  d'un `WorkItem`, décision humaine) sont tous journalisés de manière
  structurée (`structlog`) et prêts à être republiés comme événements
  de domaine dans un sprint ultérieur — voir rapport de dette
  technique.
- **Aucun agent n'accède directement à un fournisseur LLM** : vérifié
  architecturalement — `tmis.ai_team.agents.kernel_adapter` est le
  seul fichier du module à importer `TMISKernel`, et chaque agent ne
  dépend que du port étroit `KernelPort`.

## Décision structurante : unification des gabarits de mission

**Problème détecté pendant le développement** : `TeamBuilder` et
`Planner` lisaient initialement deux tables de rôles indépendantes.
Un test manuel de bout en bout a révélé qu'une équipe composée pour
`case_type="standard_analysis"` (4 rôles) ne couvrait pas les 7 rôles
que `Planner.decompose(case_type="standard_analysis")` générait par
défaut — la mission restait bloquée après les deux premières
sous-tâches, les suivantes échouant faute d'agent disponible.

**Résolution** : extraction d'une source de vérité unique,
`tmis.ai_team.capabilities.mission_templates.MISSION_TEMPLATES`,
consommée par les deux moteurs (`roles_for_case_type` pour
`TeamBuilder`, `template_for` pour `Planner`). Un test de
non-régression dédié
(`test_every_predefined_case_type_produces_a_team_matching_planner_roles`)
vérifie, pour chacun des quatre gabarits, que les rôles requis par le
plan sont un sous-ensemble des rôles présents dans l'équipe composée.

## Autre correction pendant le développement

`CoordinatorEngine._next_runnable_item` sélectionnait initialement le
prochain item via `WorkQueuePort.dequeue_next()`, qui scanne **toute**
la file — correct pour une seule mission isolée, mais incorrect dès
que la file est partagée par plusieurs missions concurrentes (le cas
en production, où `get_work_queue()` est un singleton process-wide) :
une mission aurait pu se voir attribuer l'item d'une autre. Corrigé en
filtrant d'abord sur `mission.work_item_ids` avant de choisir par
priorité — documenté explicitement dans le docstring de la méthode.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 776 fichiers
source. `pytest` : **987 tests passés, 4 ignorés** (contre 883 avant ce
sprint) — 104 tests dédiés à `ai_team` (86 unitaires + 18
d'intégration), couverture globale 95,82 %, sans qu'aucun des 883
tests précédents n'ait été modifié.

## Voir aussi

`docs/58-architecture-ai-team-platform.md` pour les diagrammes Mermaid
détaillés (composition des modules, cycle de vie d'une mission).
