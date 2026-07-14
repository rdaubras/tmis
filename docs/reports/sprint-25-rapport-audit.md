# Rapport d'audit initial — Sprint 25 (Knowledge Graph Federation & Semantic Intelligence)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (Phase 0 — ré-audit avant code). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), l'état
des neuf fichiers de référence désignés par le prompt, confirme
qu'aucun n'a dévié de l'analyse CTO, puis détermine ce qui manque
réellement.

## Phase 0 — Confirmation de non-dérive

| Fichier lu | Constat |
|---|---|
| `case_intelligence/relationships/ports.py` | `CaseGraphPort` (Protocol) : `add_node`/`add_edge`/`get_node`/`get_neighbors`, scope dossier. Inchangé. |
| `case_intelligence/relationships/schemas.py` | `CaseNode`/`CaseEdge`/`CaseNodeType` (6 types). Inchangé. |
| `case_intelligence/relationships/in_memory_graph.py` | `InMemoryCaseGraph` : dict de nodes + liste d'edges + `defaultdict` adjacency — **duplication confirmée** avec le suivant. |
| `document_intelligence/knowledge/ports.py` | `KnowledgeGraphPort` (Protocol), docstring explicite sur l'indépendance vis-à-vis de `tmis.ai.rag` (graphe vs. index vectoriel). Inchangé. |
| `document_intelligence/knowledge/builder.py` | `KnowledgeGraphBuilder.update()` peuple un `KnowledgeGraphPort` depuis layout/entités/timeline/chunks. Inchangé. |
| `document_intelligence/knowledge/in_memory_graph.py` | `InMemoryKnowledgeGraph` : même mécanisme de stockage que `InMemoryCaseGraph` — **duplication confirmée**, cible de la Phase 1. |
| `document_intelligence/schemas/knowledge.py` | `KnowledgeNode`/`KnowledgeEdge`/`NodeType` (7 types). Inchangé. |
| `cabinet_knowledge/ontology/{engine,ports,schemas,store}.py` | `OntologyEngine.link()`/`.relations_for()` sur `RelationStorePort`, scope cabinet (`firm_id`), 6 `RelationType`. Compose `cabinet_knowledge.knowledge.KnowledgeSpace` pour valider l'existence des objets liés. Inchangé. |
| `ai_governance/human_validation/*.py` | `HumanValidationEngine` : SIMPLE/MULTIPLE/HIERARCHICAL, historisé, jamais écrasé, clé par `production_id`. Réutilisable tel quel avec `production_id = ResolvedEntity.id`. Inchangé. |
| `cloud_operations/metrics/*.py` | `MetricCategory` (15 valeurs avant ce sprint, dont 5 ajoutées au Sprint 24), `MetricsEngine.record()`/`.average()`/`.history_for_category()`. Inchangé, extensible. |
| `ai_governance/policy_engine/*.py` | `GovernancePolicyType` (6 valeurs avant ce sprint), `PolicyEngine.evaluate()` en `match/case` par type. Inchangé, extensible. |
| `legal_copilot_framework/knowledge_packs/*.py` | `KnowledgePack` (pointeur versionné vers des `KnowledgeObject` ids), `KnowledgePackEngine.register_pack()`/`.resolve_objects()`. Inchangé, extensible par nouveaux champs à défaut. |
| `ai/rag/ports.py` | `IndexPort`/`ChunkerPort`/etc., `Chunk`/`RawDocument`. Le store vectoriel réel est `ai.rag.indexing.InMemoryVectorIndex` + `ai.embeddings.ports.EmbeddingProviderPort` + `ai.embeddings.similarity.cosine_similarity`. Inchangé. |

**Aucun écart constaté.** Le développement a pu commencer directement
après cette relecture.

## Composants réutilisés tels quels

| Composant existant | Ce qu'il fournit déjà | Usage dans `knowledge_graph` |
|---|---|---|
| `case_intelligence.relationships.CaseGraphPort`/`InMemoryCaseGraph` | Graphe scope dossier | Interrogé par `federation`, jamais réimplémenté |
| `document_intelligence.knowledge.KnowledgeGraphPort`/`InMemoryKnowledgeGraph` | Graphe scope document | Interrogé par `federation`, jamais réimplémenté |
| `cabinet_knowledge.ontology.OntologyEngine`/`RelationStorePort` | Graphe scope cabinet (`relations_for`) | Interrogé par `federation`, jamais réimplémenté |
| `cabinet_knowledge.knowledge.KnowledgeSpace` | Stockage tenant-scopé des objets de connaissance | Utilisé dans les tests/bootstrap pour construire un `OntologyEngine` réel |
| `cabinet_knowledge.governance.GovernanceEngine` | État DRAFT→VALIDATED historisé | Composé par `knowledge_graph.governance` pour vérifier qu'un objet référencé est validé |
| `ai_governance.human_validation.HumanValidationEngine` | Validation SIMPLE/MULTIPLE/HIERARCHICAL historisée | Route toute résolution d'entité sous le seuil de confiance |
| `ai_governance.policy_engine.PolicyEngine` | Politiques par cabinet, évaluées et expliquées | Composé par `knowledge_graph.governance` pour la visibilité d'entité restreinte |
| `cloud_operations.metrics.MetricsEngine` | Historisation de métriques par catégorie | Toutes les métriques de fédération — aucun second entrepôt |
| `legal_copilot_framework.knowledge_packs.KnowledgePackEngine` | Pointeur versionné vers des objets de connaissance | Étendu (jamais dupliqué) pour référencer entités résolues et relations fédérées |
| `ai.embeddings.EmbeddingProviderPort`/`HashingEmbeddingProvider` | Embeddings dépendance-free, déterministes | Calcule la similarité pour `semantic_intelligence`, aucun second fournisseur |
| `ai.embeddings.similarity.cosine_similarity` | Similarité cosinus | Score de chaque `SemanticLink` |

## Composants étendus (changement additif, aucune rupture)

| Composant | Extension apportée | Pourquoi une extension et non un nouveau composant |
|---|---|---|
| `cloud_operations.metrics.MetricCategory` | Ajout de `GRAPH_COVERAGE`, `ENTITY_RESOLUTION_RATE`, `SEMANTIC_LINK_DENSITY` (toutes `GAUGE`) | Un seul entrepôt de métriques historisées doit exister ; même convention que le Sprint 24 |
| `ai_governance.policy_engine.GovernancePolicyType` | Ajout de `RESTRICTED_ENTITY_VISIBILITY` + champ `restricted_entity_id` sur `GovernancePolicy`, champ `entity_id` sur `PolicyEvaluationContext`, nouvelle branche dans `PolicyEngine.evaluate()` | La restriction de visibilité d'une entité résolue est un cas de politique de gouvernance, pas un concept séparé |
| `legal_copilot_framework.knowledge_packs.KnowledgePack`/`KnowledgePackEngine.register_pack` | Ajout de `resolved_entity_ids`/`federated_relation_refs` (tuples vides par défaut, kwargs optionnels) | Le patron « pointeur, pas payload » du Sprint 24 s'étend naturellement aux entités résolues et relations fédérées, sans nouveau schéma de pack |

## Composants réellement nouveaux (aucun équivalent trouvé)

| Nouveau composant | Justification |
|---|---|
| `tmis.core.graph.AdjacencyGraphStore` (Phase 1, refactoring) | Factorise un mécanisme dupliqué à l'identique par deux classes existantes ; ne change le comportement d'aucune |
| `knowledge_graph.federation.FederationQueryEngine` | Aucune couche ne traverse aujourd'hui les trois graphes en une seule requête |
| `knowledge_graph.entity_resolution.EntityResolutionEngine`/`ResolvedEntity` | Aucun module ne décide qu'un identifiant différent dans chaque graphe désigne la même entité réelle |
| `knowledge_graph.semantic_intelligence.SemanticLinkEngine`/`SemanticLink` | Aucune relation de similarité (distincte des edges "connecté à") n'existe entre objets de connaissance de graphes différents |
| `knowledge_graph.analytics.KnowledgeGraphAnalytics` | Couche fine : trois catégories de métriques propres à la fédération, sur le moteur existant |
| `knowledge_graph.governance.KnowledgeGraphGovernance` | Couche fine : compose deux moteurs existants pour la visibilité d'entité et la validité d'un objet référencé |
| `knowledge_graph.copilot_bridge.CopilotKnowledgeBridge` | Aucun chemin n'existe pour qu'un Knowledge Pack référence des entités résolues ou des relations fédérées |
| `knowledge_graph.api` (REST, `/api/v1/knowledge-graph`) | Couche HTTP fine, même convention que tout autre bounded context exposant une API |

## Conflits d'architecture identifiés — et comment ils sont évités

1. **Trois graphes déjà existants, un quatrième explicitement interdit
   par le prompt.** Décision : `federation` ne stocke jamais un node ou
   un edge — chaque `*_neighborhood()` est une projection fine d'un
   appel existant (`get_node`/`get_neighbors`/`relations_for`). Vérifié
   par les tests d'intégration qui font traverser les trois vraies
   implémentations (`InMemoryCaseGraph`, `InMemoryKnowledgeGraph`,
   `OntologyEngine`+`InMemoryRelationStore`), jamais des doublures.
2. **Deux notions de similarité déjà proches** (`ai.rag` similarité de
   chunk pour la recherche documentaire vs. `semantic_intelligence`
   similarité entre objets de connaissance). Décision : ne pas
   dupliquer l'infrastructure vectorielle — `semantic_intelligence`
   appelle directement `EmbeddingProviderPort`/`cosine_similarity`,
   sans jamais recréer d'index. Les deux questions restent distinctes
   ("quels chunks répondent à cette requête" vs. "quels objets se
   ressemblent"), même principe que documenté dans
   `document_intelligence.knowledge.ports.KnowledgeGraphPort`.
3. **La résolution d'entité pourrait sembler recouvrir la gouvernance
   de connaissance** (`cabinet_knowledge.governance`, DRAFT→VALIDATED).
   Décision : ce sont deux questions indépendantes — une résolution
   d'entité (« ces deux occurrences sont-elles la même personne ? »)
   n'a pas de statut de gouvernance ; un objet de connaissance validé
   (« ce playbook est-il fiable ? ») n'a pas de score de confiance de
   résolution. `knowledge_graph.governance` compose les deux sans les
   fusionner.
4. **La validation humaine pourrait sembler nécessiter un mode dédié**
   pour l'entity resolution. Décision : le mode `SIMPLE` existant
   (un seul approbateur suffit) couvre exactement le besoin — aucun
   nouveau `ValidationMode` n'a été ajouté.

## Conclusion

Le développement a pu commencer directement après la Phase 0 : aucun
écart entre le code et l'analyse CTO. Les deux Phases suivantes (DRY
sur les graphes en mémoire, puis les six sous-modules de
`tmis.knowledge_graph`) n'ont nécessité que trois extensions additives
et huit composants réellement nouveaux — dont deux seulement (`entity_
resolution`, `semantic_intelligence`) sont des capacités métier
inédites au sens strict du prompt, les autres étant des couches de
composition fines. Aucun quatrième moteur de graphe n'a été créé.
