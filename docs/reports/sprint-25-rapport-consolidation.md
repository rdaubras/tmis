# Rapport de consolidation — Sprint 25 (suppression du doublon)

## Contexte

Deux implémentations concurrentes du Sprint 25 ont été développées sur
des branches séparées puis toutes deux mergées sur `main` sans que le
doublon soit détecté avant merge :

- `tmis.knowledge_graph` — « Knowledge Graph Federation & Semantic
  Intelligence » (commit `6b2212b`, PR #20) : fédère en lecture les
  trois graphes existants (`case_intelligence.relationships`,
  `document_intelligence.knowledge`, `cabinet_knowledge.ontology`)
  sans les modifier.
- `tmis.legal_knowledge_graph` — « Legal Knowledge Graph & Semantic
  Intelligence Platform » (commit `4a1fac3`, PR #19) : étend
  `cabinet_knowledge.ontology` comme substrat canonique d'un nouveau
  graphe de connaissances.

Les deux packages coexistaient dans `backend/src/tmis/`, tous deux
branchés sur `api_router`, tous deux enregistrés au même endroit de
`docs/09-roadmap-30-sprints.md` (deux entrées « Sprint 25 » dans le
tableau récapitulatif et dans le diagramme mermaid, et une note de
révision fusionnée de façon incohérente — les deux textes concaténés
sans démarcation claire, l'un des deux en-têtes ayant été perdu au
merge).

## Décision (audit CTO)

`tmis.legal_knowledge_graph` est retenu, `tmis.knowledge_graph` est
retiré, pour trois raisons :

1. **Isolation multi-tenant correcte** via `firm_id` sur chaque
   entité du graphe.
2. **Réutilisation du vocabulaire `ontology`** existant
   (`cabinet_knowledge.ontology.KnowledgeRelation`/`RelationType`,
   Sprint 12) plutôt qu'un vocabulaire de relations parallèle.
3. **Respect de la contrainte Sprint 12 sur la validation humaine** :
   seule une correspondance de nom exact (score 1.0) auto-confirme une
   résolution d'entité, tout le reste attend une décision humaine
   explicite, avec historique complet.

## Ce qui a été supprimé

### Code

- `backend/src/tmis/knowledge_graph/` en intégralité (6 sous-modules :
  `analytics`, `api`, `bootstrap.py`, `copilot_bridge`,
  `entity_resolution`, `federation`, `governance`,
  `semantic_intelligence`).
- `backend/tests/unit/knowledge_graph/` (6 fichiers de test).
- `backend/tests/integration/knowledge_graph/` (3 fichiers de test).
- Import et `include_router` de `knowledge_graph_router` dans
  `backend/src/tmis/api/v1/router.py` — seul
  `legal_knowledge_graph_router` reste monté sous `/api/v1`.

### Extensions additives orphelines

Les modules partagés que `knowledge_graph` avait étendus de façon
additive (jamais modifiés en place, donc sûrs à nettoyer isolément) :

- `backend/src/tmis/cloud_operations/metrics/schemas.py` /
  `engine.py` : retrait des 3 catégories `MetricCategory.
  GRAPH_COVERAGE`, `ENTITY_RESOLUTION_RATE`, `SEMANTIC_LINK_DENSITY`
  et de leur entrée dans `_KIND_FOR_CATEGORY`. Les 6 catégories de
  `legal_knowledge_graph` (`GRAPH_SIZE`, `SEARCH_LATENCY`,
  `ANSWER_QUALITY`, `HUMAN_VALIDATIONS`, `ENRICHMENTS`,
  `UNRESOLVED_SEARCHES`) sont conservées.
- `backend/src/tmis/ai_governance/policy_engine/schemas.py` /
  `engine.py` : retrait de `GovernancePolicyType.
  RESTRICTED_ENTITY_VISIBILITY`, du champ `GovernancePolicy.
  restricted_entity_id`, du champ `PolicyEvaluationContext.entity_id`
  et du `case` correspondant dans `PolicyEngine.evaluate()` — cette
  politique n'avait aucun appelant en dehors de
  `knowledge_graph.governance`, confirmé par recherche exhaustive dans
  le code et les tests avant suppression.
- `backend/src/tmis/legal_copilot_framework/knowledge_packs/
  schemas.py` / `engine.py` : retrait des champs
  `KnowledgePack.resolved_entity_ids` / `.federated_relation_refs`
  (et des paramètres correspondants de
  `KnowledgePackEngine.register_pack`) — l'intégration Copilotes de
  `legal_knowledge_graph` utilise un chemin distinct
  (`CopilotContext.graph_context` via `copilot_bridge.
  attach_graph_context`), donc ces champs étaient sans producteur ni
  consommateur après suppression de `knowledge_graph`.

Aucune de ces trois extensions n'était couverte par un test — leur
suppression a été vérifiée par recherche exhaustive de chaque symbole
avant retrait, conformément à la consigne de vérification de la
mission.

### Documentation

- `docs/145-architecture-knowledge-graph.md`
- `docs/146-guide-entity-resolution.md`
- `docs/147-guide-semantic-intelligence.md`
- `docs/148-reference-api-knowledge-graph.md`
- `docs/reports/sprint-25-rapport-audit.md` et
  `docs/reports/sprint-25-rapport-architecture.md` — ces deux rapports
  documentaient exclusivement `knowledge_graph` (Phase 0, table des 9
  fichiers de référence, décomposition en 6 sous-modules) ; les
  conserver aurait laissé des références permanentes au package
  supprimé, contraire à l'exigence de vérification finale de la
  mission. **Note** : le rapport d'audit équivalent côté
  `legal_knowledge_graph` portait le même nom de fichier
  (`sprint-25-rapport-audit.md`) ; l'une des deux versions a été
  perdue lors du merge sur `main` (seule la version côté
  `knowledge_graph` avait survécu). Il n'existe donc plus de rapport
  d'audit/architecture dédié pour `legal_knowledge_graph` — seul
  `docs/reports/sprint-25-demo-legal-knowledge-graph.md` (démonstration
  avec sorties réelles) subsiste, conservé tel quel.

Documents conservés sans changement de contenu (renumérotés/déplacés
par personne, déjà au bon numéro) :
`docs/145-architecture-legal-knowledge-graph.md`,
`docs/146-guide-ingestion-knowledge-graph.md`,
`docs/147-guide-validation-humaine-graphe.md`,
`docs/148-guide-gouvernance-knowledge-graph.md`,
`docs/149-guide-creation-knowledge-pack.md`,
`docs/150-reference-api-legal-knowledge-graph.md`.

Deux références résiduelles à un fichier supprimé ont été corrigées :

- `docs/145-architecture-legal-knowledge-graph.md` citait
  `docs/reports/sprint-25-rapport-audit.md` et
  `docs/reports/sprint-25-rapport-architecture.md` (les deux fichiers
  perdus au merge, cf. ci-dessus) — citations retirées.
- `docs/reports/sprint-25-demo-legal-knowledge-graph.md` citait les
  deux mêmes fichiers — citations retirées.
- Les docstrings de `InMemoryKnowledgeGraph`
  (`document_intelligence/knowledge/in_memory_graph.py`) et
  `InMemoryCaseGraph` (`case_intelligence/relationships/
  in_memory_graph.py`) pointaient vers
  `docs/145-architecture-knowledge-graph.md` (supprimé) — la citation
  a été retirée, le texte explicatif conservé.

### `docs/09-roadmap-30-sprints.md`

La note de révision « après Sprint 25 » racontait jusqu'ici deux
histoires concaténées (celle de `knowledge_graph`, puis celle de
`legal_knowledge_graph` sans en-tête propre — artefact du merge). Elle
a été réécrite pour ne raconter que l'histoire de
`legal_knowledge_graph` : audit des trois graphes fragmentés, décision
d'étendre `cabinet_knowledge.ontology`, puis description du nouveau
package. Le paragraphe sur la Phase 1 de refactoring DRY
(`AdjacencyGraphStore`) a été conservé et clairement présenté comme
indépendant du choix d'architecture qui suit (voir section suivante).

Le tableau récapitulatif et le diagramme mermaid contenaient chacun
deux entrées « Sprint 25 » (une par implémentation) ; l'entrée
`Knowledge Graph Federation & Semantic Intelligence` a été retirée des
deux, ne laissant que `Legal Knowledge Graph & Semantic Intelligence
Platform`. La citation de fin de ligne du tableau a été corrigée pour
ne plus référencer le rapport d'audit disparu.

## Ce qui N'A PAS été touché : Phase 1 (refactoring DRY)

La Phase 1 du Sprint 25 — factorisation de `AdjacencyGraphStore`
générique dans `tmis.core.graph` (`backend/src/tmis/core/graph/
adjacency_store.py`), composé par délégation dans
`InMemoryCaseGraph` (`case_intelligence.relationships`) et
`InMemoryKnowledgeGraph` (`document_intelligence.knowledge`) — a été
introduite dans le commit `6b2212b` (celui de `knowledge_graph`), mais
elle est **indépendante du choix entre les deux packages** : elle ne
touche que les deux graphes en mémoire pré-existants des Sprints 3 et
4, et n'est utilisée par aucun des deux nouveaux packages Sprint 25
(`legal_knowledge_graph.graph_core` a sa propre implémentation de
stockage, distincte, car son substrat est `cabinet_knowledge.ontology`
et non les deux graphes en mémoire).

Vérifié : `tmis.core.graph` n'a pas été supprimé, `AdjacencyGraphStore`
reste composé par les deux classes `InMemory*Graph`, et
`legal_knowledge_graph` n'en dépend pas — sa suppression n'était donc
ni nécessaire ni souhaitable.

## Vérification finale

- `uv run ruff check .` : 1 erreur, préexistante et sans rapport avec
  ce travail (`alembic/env.py`, import non trié) — identique avant et
  après cette consolidation.
- `uv run mypy src` : aucune erreur (1846 fichiers).
- `uv run pytest` : **1961 tests passés, 4 skippés** — exactement le
  compte attendu pour `legal_knowledge_graph` seul (1903 tests
  préexistants + 58 tests dédiés), confirmant que les 43 tests de
  `knowledge_graph` ont bien disparu sans effet de bord sur le reste
  de la suite.
- `grep -r "tmis.knowledge_graph"` sur tout le dépôt (code, docs,
  scripts) : aucune occurrence restante (hors caches d'outils
  non versionnés, purgés).
- OpenAPI généré par `tmis.main.app` : 365 routes, toutes sous
  `/api/v1/legal-knowledge-graph/*` pour ce domaine — aucune route
  `knowledge-graph` (sans `legal-`) résiduelle.

## Fichiers modifiés (résumé)

51 fichiers touchés (hors ce rapport), +20/-3082 lignes :

- 30 fichiers supprimés dans `backend/src/tmis/knowledge_graph/` et
  ses tests.
- 6 fichiers de documentation supprimés
  (4 docs numérotés + 2 rapports).
- 7 fichiers de code modifiés (router, métriques, gouvernance,
  knowledge packs, 2 docstrings de graphes en mémoire).
- 3 fichiers de documentation modifiés (roadmap, architecture
  `legal_knowledge_graph`, démo).
