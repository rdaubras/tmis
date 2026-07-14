# Rapport d'architecture — Sprint 25 (Knowledge Graph Federation & Semantic Intelligence)

## Résumé

Le Sprint 25 ajoute `backend/src/tmis/knowledge_graph/` (6 sous-modules
+ une couche API, 14 endpoints REST, 40 tests dédiés), précédé d'une
Phase 1 de refactoring DRY sur les deux graphes en mémoire existants.
Le prompt utilisateur imposait une Phase 0 de ré-audit direct des
fichiers concernés avant tout code, et interdisait explicitement la
création d'un quatrième moteur de graphe ; cet audit
(docs/reports/sprint-25-rapport-audit.md) confirme qu'aucun des neuf
fichiers de référence n'avait dévié de l'analyse CTO, et a directement
déterminé la portée : composer les trois graphes existants et cinq
autres composants, étendre trois enums/schémas de façon additive, et
ne construire que deux capacités métier réellement nouvelles
(`entity_resolution`, `semantic_intelligence`) plus quatre couches de
composition fines (`federation`, `analytics`, `governance`,
`copilot_bridge`).

Points de contact hors `knowledge_graph/` :

- `tmis/core/graph/adjacency_store.py` — nouveau module (Phase 1),
  `AdjacencyGraphStore(Generic[NodeT, EdgeT])`, contraint par deux
  protocoles structurels (`_HasId`, `_HasEndpoints`) plutôt que par les
  dataclasses concrètes, pour rester indépendant du vocabulaire de
  chaque graphe.
- `tmis/case_intelligence/relationships/in_memory_graph.py` et
  `tmis/document_intelligence/knowledge/in_memory_graph.py` —
  réécrits pour composer `AdjacencyGraphStore` par délégation ; ports
  et tests existants inchangés.
- `tmis/cloud_operations/metrics/schemas.py` et `engine.py` — trois
  nouvelles catégories `MetricCategory` (`GRAPH_COVERAGE`,
  `ENTITY_RESOLUTION_RATE`, `SEMANTIC_LINK_DENSITY`, toutes `GAUGE`) et
  leur mapping.
- `tmis/ai_governance/policy_engine/schemas.py` et `engine.py` —
  nouveau `GovernancePolicyType.RESTRICTED_ENTITY_VISIBILITY`, champs
  additifs `GovernancePolicy.restricted_entity_id`/
  `PolicyEvaluationContext.entity_id`, nouvelle branche dans
  `PolicyEngine.evaluate()`.
- `tmis/legal_copilot_framework/knowledge_packs/schemas.py` et
  `engine.py` — champs additifs `KnowledgePack.resolved_entity_ids`/
  `.federated_relation_refs` (tuples vides par défaut),
  `KnowledgePackEngine.register_pack()` accepte les deux en kwargs
  optionnels.
- `tmis/api/v1/router.py` — montage de `knowledge_graph_router` sous
  `/api/v1`.

## Conformité aux principes architecturaux

- **Phase 0 obligatoire avant code** : ré-audit direct des neuf
  fichiers désignés par le prompt (docs/reports/sprint-25-rapport-audit.md),
  aucun écart constaté, comme l'exigeait le prompt lui-même.
- **Phase 1 : DRY sans rupture** : `AdjacencyGraphStore` factorise un
  mécanisme dupliqué à l'identique par `InMemoryCaseGraph` et
  `InMemoryKnowledgeGraph` ; composition par délégation (jamais
  héritage), ports inchangés, tous les tests antérieurs sur ces deux
  modules passent sans modification.
- **Zéro stockage de nodes/edges bruts dans `knowledge_graph/`** :
  `federation.FederationQueryEngine` ne détient aucun état — chaque
  méthode est une projection fine d'un appel existant
  (`CaseGraphPort.get_node`/`.get_neighbors`,
  `KnowledgeGraphPort.get_node`/`.get_neighbors`,
  `OntologyEngine.relations_for`). `entity_resolution` ne stocke que
  l'issue de la résolution (`ResolvedEntity`) ; `semantic_intelligence`
  ne stocke que des `SemanticLink`, un type distinct des edges des
  trois graphes.
- **Composer, ne jamais reconstruire** : `entity_resolution` route
  toute résolution sous le seuil de confiance vers
  `ai_governance.human_validation.HumanValidationEngine` (mode
  `SIMPLE`) plutôt que de construire un second mécanisme de validation.
  `semantic_intelligence` appelle `ai.embeddings.EmbeddingProviderPort`/
  `cosine_similarity` plutôt qu'un second fournisseur d'embeddings ou
  un second index vectoriel. `analytics` et `governance` composent
  respectivement `cloud_operations.metrics.MetricsEngine` et
  `ai_governance.policy_engine.PolicyEngine` +
  `cabinet_knowledge.governance.GovernanceEngine`.
- **Le patron « pointeur, pas payload »** (Sprint 24) : `copilot_bridge`
  n'ajoute que des ids (`resolved_entity_ids`, `federated_relation_refs`)
  au `KnowledgePack`, résolus fraîchement à chaque appel via
  `EntityResolutionEngine`/`FederationQueryEngine` — jamais une copie.
- **Multi-tenant strict** : chaque appel touchant l'état d'un cabinet
  passe un `firm_id`, y compris à travers `federation.
  cross_scope_neighborhood` (le paramètre est utilisé pour
  `OntologyEngine.relations_for`, scope cabinet).

## Conflits d'architecture — rappel et confirmation

Voir la section « Conflits d'architecture identifiés » de l'audit
(docs/reports/sprint-25-rapport-audit.md) pour le détail des quatre
zones de recouvrement apparent identifiées et tranchées avant
l'implémentation ; aucune déviation constatée pendant le développement.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `core.graph.AdjacencyGraphStore` | (Phase 1, factorisation interne) | le comportement de `InMemoryCaseGraph`/`InMemoryKnowledgeGraph`, qui reste identique |
| `federation.FederationQueryEngine` | `CaseGraphPort`, `KnowledgeGraphPort`, `OntologyEngine` (S4, S3, S12) | le stockage/traversal des trois graphes |
| `entity_resolution.EntityResolutionEngine` | `ai_governance.human_validation.HumanValidationEngine` (S15) | l'approbation humaine (mode `SIMPLE` réutilisé tel quel) |
| `semantic_intelligence.SemanticLinkEngine` | `ai.embeddings.EmbeddingProviderPort`/`cosine_similarity` (S2) | le fournisseur d'embeddings, l'index vectoriel |
| `analytics.KnowledgeGraphAnalytics` | `cloud_operations.metrics.MetricsEngine` (S21) | le stockage de métriques historisées |
| `governance.KnowledgeGraphGovernance` | `ai_governance.policy_engine.PolicyEngine` (S15), `cabinet_knowledge.governance.GovernanceEngine` (S12) | l'évaluation de politique, le cycle de vie de la connaissance |
| `copilot_bridge.CopilotKnowledgeBridge` | `legal_copilot_framework.knowledge_packs.KnowledgePackEngine` (S24), `entity_resolution`, `federation` | le stockage/versionnage de Knowledge Pack |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` → Success, 1827 fichiers source (aucune erreur)
- `pytest -q` → 1943 passed, 4 skipped (1903 tests précédents + 40
  nouveaux : 32 unitaires, 8 intégration dont 5 API end-to-end)

## Corrections apportées pendant la vérification

- Les protocoles structurels `_HasId`/`_HasEndpoints` d'
  `AdjacencyGraphStore` déclaraient d'abord `id`/`source_id`/
  `target_id` comme attributs simples — `mypy` a rejeté
  `CaseNode`/`KnowledgeNode` (dataclasses `frozen=True`) comme
  sous-types, un attribut de protocole simple étant traité comme
  accessible en écriture. Corrigé en déclarant ces membres en
  `@property` en lecture seule, compatible avec des champs de
  dataclass gelée.
- `federation.engine.cabinet_neighborhood` calculait deux fois la même
  expression conditionnelle (`node_id`/`label`) sur une seule ligne
  trop longue pour `ruff` (E501) ; extrait dans une variable `other_id`
  avant construction du `FederatedNodeRef`, plus lisible et plus court.
