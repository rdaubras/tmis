# Rapport d'architecture — Sprint 25 (Legal Knowledge Graph & Semantic Intelligence Platform)

## Résumé

Le Sprint 25 ajoute `backend/src/tmis/legal_knowledge_graph/` (11
sous-modules, 13 endpoints REST, 58 tests dédiés). Le prompt
utilisateur exigeait une Phase 1 d'audit exhaustif avant toute
implémentation ; cet audit (docs/reports/sprint-25-rapport-audit.md)
a révélé que **trois graphes de connaissances existaient déjà**,
fragmentés et sans unification (`document_intelligence.knowledge`,
scope un document ; `case_intelligence.relationships`, scope un
dossier ; `cabinet_knowledge.ontology`, seul fragment multi-tenant
mais restreint aux relations entre deux `KnowledgeObject`). La
décision d'architecture centrale du sprint découle directement de ce
constat : étendre `cabinet_knowledge.ontology` plutôt que construire
un quatrième moteur de graphe.

Points de contact hors `legal_knowledge_graph/` :

- `tmis/cabinet_knowledge/ontology/schemas.py` — `RelationType` gagne
  quatre membres additifs (`INFLUENCES`, `APPEARS_IN`, `MENTIONS`,
  `SAME_AS`) ; `KnowledgeRelation` gagne deux champs optionnels
  (`explanation: str | None = None`, `confidence: float = 1.0`),
  défaut neutre pour ne casser aucun appelant Sprint 12 existant.
- `tmis/cabinet_knowledge/knowledge/schemas.py` — `KnowledgeType`
  gagne `CONTRACT` (un contrat entier n'a pas d'équivalent parmi les
  types existants : `CLAUSE` ne couvre qu'une seule clause).
- `tmis/identity_platform/permissions/schemas.py` — ajout de
  `Permission.KNOWLEDGE_GRAPH_MANAGE`.
- `tmis/identity_platform/rbac/schemas.py` — `KNOWLEDGE_GRAPH_MANAGE`
  accordé aux rôles `PARTNER`, `ASSOCIATE` et `IT_ADMIN` dans
  `DEFAULT_ROLE_PERMISSIONS`, **dans le même commit** que l'ajout de
  la permission — leçon tirée directement du bug du Sprint 24
  (`COPILOT_MANAGE` avait été ajouté sans être accordé à aucun rôle).
- `tmis/cloud_operations/metrics/schemas.py` et `engine.py` — six
  nouvelles catégories `MetricCategory` (`GRAPH_SIZE`,
  `SEARCH_LATENCY`, `ANSWER_QUALITY`, `HUMAN_VALIDATIONS`,
  `ENRICHMENTS`, `UNRESOLVED_SEARCHES`) et leur mapping vers
  `MetricKind`.
- `tmis/legal_copilot_framework/context_engine/schemas.py` —
  `CopilotContext` gagne un champ optionnel `graph_context: dict[str,
  tuple[str, ...]] = field(default_factory=dict)`, rempli exclusivement
  par `legal_knowledge_graph.copilot_bridge.attach_graph_context`
  (jamais par `ContextEngine` lui-même, qui reste libre de toute
  dépendance vers un package créé après lui).
- `tmis/api/v1/router.py` — montage de
  `legal_knowledge_graph_router` sous `/api/v1`.

## Conformité aux principes architecturaux

- **Phase 1 obligatoire avant code** : un rapport d'audit dédié
  (docs/reports/sprint-25-rapport-audit.md) a précédé toute
  implémentation, comme l'exigeait le prompt du sprint lui-même.
- **Aucun graphe concurrent** : les trois graphes fragmentés
  identifiés par l'audit ne sont ni dupliqués ni remplacés —
  `document_intelligence.knowledge` et `case_intelligence.
  relationships` restent des implémentations locales inchangées,
  qui alimentent le nouveau graphe uniquement via l'ingestion.
- **Le patron « pointeur, pas payload »** (hérité du Sprint 24,
  réappliqué ici) : `GraphNode.ref_id` est l'id de l'entité réelle
  dans son contexte propriétaire — jamais une copie de contenu.
  Résoudre `ref_id` reste toujours la responsabilité de l'appelant.
- **Extension additive du vocabulaire de relations** : `RelationType`
  et `KnowledgeRelation` (Sprint 12) sont étendus, jamais dupliqués —
  même les relations entre nœuds qui ne sont pas des `KnowledgeObject`
  (un `CASE`, un `ARGUMENT`) utilisent le même vocabulaire, seul le
  stockage (`GraphRelationStorePort`) est nouveau.
- **Aucune connaissance sans validation humaine** : seule une
  correspondance de nom normalisé exact (score 1.0) auto-confirme une
  relation `SAME_AS` (`_AUTO_CONFIRM_THRESHOLD = 0.98`) ; l'ingestion
  ne publie jamais automatiquement (`publish()` reste un appel humain
  distinct de `submit_for_validation()`, comme `cabinet_knowledge.
  approval` l'exige depuis le Sprint 12).
- **Gouvernance déléguée, jamais réimplémentée** :
  `GraphAccessPolicyEngine` ne porte que des métadonnées
  (confidentialité, rétention) — la décision d'accès/modification/
  publication reste entièrement celle d'`identity_platform.api.guard.
  authorize_or_403` (RBAC + ABAC + Zero Trust, Sprint 19).

## Conflits d'architecture anticipés et résolus

1. **Portée de la traçabilité.** `ai_governance.provenance`/
   `.traceability`/`.audit` (Sprint 15) tracent des *productions IA*
   (un brouillon généré) ; `cabinet_knowledge.lineage` (Sprint 12)
   trace des *objets de connaissance*. Le Knowledge Graph reste sur
   la traçabilité d'objets de connaissance, jamais fusionnée avec la
   traçabilité de productions IA — même distinction que celle actée
   entre Reasoning Packs et `legal_reasoning` au Sprint 24.
2. **Déclaration vs exécution du raisonnement.** Les nœuds ARGUMENT
   et la requête `historical_reasonings` sont purement déclaratifs —
   aucune logique de raisonnement n'est réimplémentée ; `legal_
   reasoning` reste seul exécuteur.
3. **Validation d'un sujet non-`KnowledgeObject`.** `cabinet_
   knowledge.feedback.FeedbackEngine` exige que `KnowledgeSpace.get`
   résolve le sujet — impossible pour un `GraphNode` CASE/PARTY/
   ARGUMENT qui pointe vers un autre contexte. `human_validation.
   GraphFeedbackEngine` réutilise le même vocabulaire `FeedbackAction`
   mais avec un store propre au sujet, plutôt que de forcer chaque
   nœud du graphe à devenir un `KnowledgeObject`.
4. **Intégration Copilotes sans coupler le Sprint 24.** Plutôt que
   d'ajouter une dépendance au constructeur de `ContextEngine`
   (cassant tout appelant existant qui ne fournit pas de graphe), un
   champ optionnel défaulté (`graph_context`) et une fonction pont
   pure (`attach_graph_context`) permettent d'enrichir un
   `CopilotContext` déjà construit — un copilote fonctionne avec ou
   sans le graphe.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `graph_core.GraphEngine` | `cabinet_knowledge.ontology.KnowledgeRelation`/`RelationType` (S12) | vocabulaire de relations |
| `semantic_engine.SemanticEngine` | `ai.embeddings.HashingEmbeddingProvider`/`.similarity` (S2), `document_intelligence.classification` (S3) | modèle d'embeddings, classification |
| `entity_resolution.EntityResolutionEngine` | `case_intelligence.actors.merger.normalize_name` (S4), `ai_governance.human_validation.HumanValidationEngine` (S15) | normalisation de nom, validation humaine formelle |
| `ingestion.KnowledgeIngestionPipeline` | `cabinet_knowledge.knowledge.KnowledgeSpace`/`.lineage`/`.validation`/`.approval` (S12), `document_intelligence.entities.RegexEntityExtractor` (S3) | stockage, gouvernance, extraction d'entités |
| `human_validation.GraphFeedbackEngine` | `cabinet_knowledge.feedback.FeedbackAction` (S12, vocabulaire) | mécanisme de feedback pour un `KnowledgeObject` (reste `FeedbackEngine`) |
| `copilot_bridge` | `legal_copilot_framework.context_engine.CopilotContext` (S24) | construction du contexte copilote |
| `governance.GraphAccessPolicyEngine` | `identity_platform.api.guard.authorize_or_403`, `.abac.AbacAttributes` (S19) | décision d'autorisation |
| `quality.GraphQualityEngine` | `cabinet_knowledge.quality.QualityEngine` (S12) | calcul du score de base (fraîcheur, complétude, usage) |
| `analytics.GraphAnalyticsEngine` | `cloud_operations.metrics.MetricsEngine` (S21) | stockage de métriques historisées |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` → Success, 1844 fichiers source (aucune erreur)
- `pytest -q` → 1961 passed, 4 skipped (1903 tests précédents + 58
  nouveaux : 45 unitaires, 13 intégration)

## Corrections apportées pendant la vérification

- `bootstrap.py::get_knowledge_graph_query_engine` dépassait 100
  caractères sur une ligne (E501) après la composition à trois
  dépendances — corrigé en repliant l'appel sur plusieurs lignes,
  motif déjà appliqué à répétition dans ce sprint (`graph_core.
  engine`, `ingestion.engine`, `copilot_bridge.engine`, `quality.
  engine`, `analytics.engine`).
- Le texte de démonstration initial utilisait « ACME Corp Sarl »
  (casse mixte) comme variante de nom pour tester la résolution
  d'entités — `document_intelligence.entities.RegexEntityExtractor`
  n'extrait les sociétés que sur un suffixe en majuscules
  (`SARL`/`SAS`/...), donc cette variante n'aurait jamais été
  reconnue comme entité lors de l'ingestion. Corrigé en « ACME CORP
  SARL » (variante de casse qui reste détectée, `normalize_name`
  produisant la même forme normalisée que l'original).
- `api/routes.py::node_neighbors` retournait `200` avec une liste
  vide pour un `node_id` inexistant plutôt que `404`, car
  `GraphEngine.neighbors()` ne valide l'existence du nœud interrogé
  que s'il a au moins une relation. Corrigé en appelant explicitement
  `GraphEngine.get_node()` avant `neighbors()`, pour un contrat REST
  cohérent avec `GET /nodes/{id}/quality` (qui, lui, appelle déjà
  `evaluate()` → `get_node()`).
- Deux fichiers de test nommés `test_ingestion.py` (un dans
  `tests/unit/document_intelligence/`, un dans `tests/unit/
  legal_knowledge_graph/`) provoquaient une collision de module
  pytest (aucun `__init__.py` dans `tests/`, donc les noms de base
  doivent être uniques dans tout le dépôt). Renommé en
  `test_ingestion_pipeline.py`.
