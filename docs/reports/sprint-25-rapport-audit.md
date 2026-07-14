# Rapport d'audit — Sprint 25 (Legal Knowledge Graph & Semantic Intelligence Platform)

## Méthode

Conformément à l'instruction du prompt ("avant toute implémentation :
analyser complètement le dépôt"), cet audit précède tout code. Il
recense les capacités existantes du Knowledge Engine, les modèles de
données actuels, les systèmes de recherche disponibles, les
embeddings existants, le stockage vectoriel éventuel, et les
composants réutilisables.

## Constat central : trois fragments de graphe déjà existants, jamais unifiés

L'audit a trouvé **trois implémentations de graphe indépendantes**,
chacune scopée à un seul bounded context, jamais fédérées :

| Fragment | Localisation | Portée | Nœuds | Arêtes |
|---|---|---|---|---|
| Knowledge graph documentaire | `document_intelligence.knowledge` (Sprint 3) | Un seul document, en mémoire, jamais persisté au-delà du pipeline | `NodeType` : DOCUMENT, SECTION, ENTITY, DATE, EVENT, REFERENCE, CHUNK | `KnowledgeEdge(source_id, target_id, relation: str)` — relation en texte libre |
| Graphe de dossier | `case_intelligence.relationships` (Sprint 4) | Un seul dossier, en mémoire | `CaseNodeType` : ACTOR, DOCUMENT, EVENT, FACT, EXHIBIT, ISSUE | `CaseEdge(source_id, target_id, relation: str)` — relation en texte libre |
| Ontologie de connaissances | `cabinet_knowledge.ontology` (Sprint 12) | **Multi-tenant** (`firm_id`), entre `KnowledgeObject`s uniquement | Implicite (l'objet `KnowledgeObject` lui-même) | `KnowledgeRelation(source_id, target_id, relation_type: RelationType)` — vocabulaire fermé : CITES, SUPERSEDES, DERIVED_FROM, RELATED_TO, CONTRADICTS, APPLIES_TO |

Aucun des trois ne répond seul au besoin du sprint (un graphe
multi-tenant couvrant documents, dossiers, jurisprudences, contrats,
clauses, parties, personnes morales, arguments, risques, procédures).
**La décision architecturale de ce sprint est de ne pas créer un
quatrième graphe concurrent**, mais d'étendre le seul fragment déjà
multi-tenant et gouverné — `cabinet_knowledge.ontology` — avec une
notion de nœud générique (pointeur vers une entité vivant dans
n'importe quel bounded context), tout en laissant les deux graphes
locaux (document/dossier) intacts comme sources d'ingestion.

## Capacités de recherche et d'embeddings déjà réelles

| Composant | Rôle | Réutilisable tel quel |
|---|---|---|
| `ai.embeddings.HashingEmbeddingProvider` | Embedding déterministe bag-of-words (dimension configurable), `EmbeddingProviderPort` | Oui — c'est l'embedding réel de tout TMIS aujourd'hui, en attendant un vrai modèle (Sprint 26 de la roadmap) |
| `ai.embeddings.similarity.cosine_similarity` | Similarité cosinus entre deux vecteurs | Oui |
| `ai.rag.InMemoryVectorIndex` | Recherche par similarité cosinus, brute-force, `IndexPort.upsert/search`, filtres par métadonnées | Le *mécanisme* est réutilisable ; le schéma `Chunk`/`RetrievedChunk` est scopé documents — le Sprint 25 a besoin d'un index scopé nœuds de graphe, construit avec la même logique (pas de nouvelle techno vectorielle) |
| `ai.retrieval.HybridRetriever` | Combine similarité vectorielle et recouvrement lexical | Le patron (hybridation vecteur+lexical) est repris pour la recherche par intention ; pas d'appel direct car scopé `RetrievedChunk` |
| `cabinet_knowledge.search.SearchEngine` | Recherche multi-critères sur `KnowledgeSpace` (tag, statut, mot-clé) | Oui — reste la recherche de référence sur les `KnowledgeObject` |
| `cabinet_knowledge.recommendations.RecommendationEngine` | Recommandation explicable (score + raisons textuelles) | Oui — le patron d'explicabilité est repris pour les relations du graphe |
| `legal_research.search`/`.ranking` | Recherche juridique hybride, pondérée, avec citations | Hors périmètre direct (recherche externe), mais confirme qu'aucun moteur de recherche sémantique générique n'existe encore dans le dépôt |
| **Stockage vectoriel** | — | **Aucun** stockage vectoriel réel (Qdrant) n'existe encore ; `InMemoryVectorIndex` en tient lieu partout, y compris pour ce sprint |

## Gouvernance, validation, qualité et traçabilité déjà réelles

| Composant | Rôle | Extension nécessaire pour ce sprint |
|---|---|---|
| `cabinet_knowledge.governance.GovernanceEngine` | Machine à états DRAFT→IN_REVIEW→VALIDATED→OBSOLETE→ARCHIVED, historisée | Aucune — réutilisé tel quel pour tout nœud qui est un `KnowledgeObject` |
| `cabinet_knowledge.validation.ValidationEngine` | Boucle de validation humaine ("aucune connaissance ne peut être ajoutée sans validation humaine") | Aucune — c'est la boucle de validation humaine du Sprint 25 (Phase 6) pour les `KnowledgeObject` |
| `cabinet_knowledge.feedback.FeedbackEngine` + `FeedbackAction` (ACCEPT/MODIFY/REJECT/ANNOTATE/EXPLAIN) | Annotation/correction/rejet, alimente le score de qualité | Réutilisé directement ; `FeedbackAction` couvre déjà exactement les actions demandées par la Phase 6 |
| `cabinet_knowledge.approval.ApprovalEngine` | Publication (deuxième porte après validation) | Aucune — réutilisé pour "publication dans le Knowledge Graph" (fin du pipeline d'ingestion, Phase 5) |
| `cabinet_knowledge.lineage.LineageEngine` | Provenance et historique de révision d'un `KnowledgeObject` | Aucune — traçabilité de "toute connaissance" (contrainte du sprint) déjà fournie ici |
| `cabinet_knowledge.quality.QualityEngine` | Score de qualité (fraîcheur, complétude, usage, validation humaine, cohérence) | **Étendue** (Phase 9) : doublons (via Entity Resolution), incohérences (via `RelationType.CONTRADICTS`), sources manquantes (via `LineageEngine`) — jamais un second moteur de score |
| `ai_governance.human_validation.HumanValidationEngine` | Validation simple/multiple/hiérarchique, déjà réutilisée par le Legal Copilot Framework (Sprint 24) | Réutilisée pour les décisions de résolution d'entités à faible confiance |
| `ai_governance.provenance`/`.traceability` | Traçabilité d'une *production IA* (brouillon généré) | Hors périmètre direct : portée différente (une production, pas une connaissance) — non dupliqué, non réutilisé directement |
| `ai_governance.audit.AIAuditEngine` | Journal d'audit d'une production IA | Hors périmètre direct, même raison |
| `case_intelligence.actors.merger.ActorMerger`/`normalize_name` | Fusion déterministe d'acteurs par nom normalisé + alias, scopée à un dossier | **Précédent architectural** pour la Phase 4 (Entity Resolution) — le patron (normalisation + alias + fusion) est repris et généralisé avec score et validation humaine ; le code lui-même reste local à `case_intelligence` |

## Identité, sécurité et confidentialité déjà réels

| Composant | Rôle | Réutilisation prévue |
|---|---|---|
| `identity_platform.tenant_context` | Isolation stricte par `firm_id`, déjà le socle multi-tenant de tout TMIS | Chaque nœud/relation du graphe est `firm_id`-scopé, comme tout le reste du dépôt |
| `identity_platform.abac.AbacAttributes` | `confidentiality_level`, `case_id`, `client_id`, `department_id` | Réutilisé directement pour "niveau de confidentialité" (Phase 8) — pas de second vocabulaire de confidentialité |
| `identity_platform.rbac`/`.authorization` | RBAC + ABAC + Zero Trust | Réutilisé pour "qui peut voir/modifier/publier" |
| `ai_governance.policy_engine.PolicyEngine` | Politiques par firme, déjà étendu par le Sprint 24 (`RESTRICTED_TO_ROLE`) | Réutilisé pour les politiques de gouvernance du graphe |
| `identity_platform.api.guard.authorize_or_403` | Point d'entrée unique d'autorisation pour toute API | Chaque endpoint mutateur du Sprint 25 l'appelle, comme tous les sprints précédents |

## Copilots et observabilité déjà réels

| Composant | Rôle | Réutilisation prévue |
|---|---|---|
| `legal_copilot_framework.context_engine.ContextEngine` (Sprint 24) | Agrège contexte utilisateur/cabinet/dossier pour un copilote | **Étendu de façon additive** (Phase 7) : un nouveau champ optionnel sur `CopilotContext`, rempli par un pont pur (`copilot_bridge`), sans toucher la logique de `ContextEngine.build()` |
| `legal_copilot_framework.knowledge_packs`/`.reasoning_packs` (Sprint 24) | Pointeurs versionnés vers des `KnowledgeObject`/patterns de raisonnement | Le graphe devient une source supplémentaire de résolution pour ces packs, jamais un remplacement |
| `cloud_operations.metrics.MetricsEngine` + `MetricCategory` | Métriques historisées, déjà étendu par les Sprints 22 et 24 | Étendu une nouvelle fois (Phase 10) avec des catégories propres au graphe — même patron additif |
| `runtime_platform.distributed_cache`/`.event_store` (Sprint 23) | Cache distribué décorant `ai.cache.CachePort`, Event Sourcing générique | Réutilisables en option pour la performance de recherche sémantique et l'historisation des enrichissements — non indispensables au MVP démonstratif de ce sprint |

## Composants réellement nouveaux

| Composant | Justification |
|---|---|
| `graph_core.GraphNode` / `GraphRelation` / `GraphEngine` | Aucun fragment existant n'est à la fois multi-tenant et cross-context ; nécessaire pour unifier les trois graphes locaux sans les dupliquer |
| `semantic_engine.SemanticEngine` | Couche d'orchestration au-dessus de `ai.embeddings`/`ai.rag` scopée aux nœuds du graphe (pas aux chunks documentaires) |
| `entity_resolution.EntityResolutionEngine` | Généralise `case_intelligence.actors.merger` avec scoring, validation humaine et historique, à l'échelle du cabinet plutôt que d'un seul dossier |
| `ingestion.KnowledgeIngestionPipeline` | Orchestrateur Import→Extraction→Classification→Enrichissement→Validation→Publication ; chaque étape délègue à un moteur existant |
| `human_validation.GraphFeedbackEngine` | Adapte `cabinet_knowledge.feedback.FeedbackAction` (réutilisé, pas dupliqué) aux sujets propres au graphe (relations, résolutions d'entités) |
| `copilot_bridge.KnowledgeGraphQueryEngine` | Traduit une requête copilote (connaissances pertinentes, documents similaires, raisonnements historiques, modèles validés, risques) en requêtes de graphe |
| `governance.GraphAccessPolicyEngine` | Combine ABAC/RBAC existants avec une politique de rétention/confidentialité par nœud — absent ailleurs |
| `quality.GraphQualityEngine` | Étend `QualityEngine` avec la détection de doublons/incohérences/sources manquantes propre au graphe |
| `analytics.GraphAnalyticsEngine` | Composition fine sur `MetricsEngine`, nouvelles catégories seulement |

## Conflits d'architecture anticipés et leur résolution

1. **Trois graphes existants** — résolu en étendant `cabinet_knowledge.ontology` (déjà multi-tenant) plutôt que `document_intelligence.knowledge` ou `case_intelligence.relationships` (tous deux non multi-tenant, scopés à une seule entité). Ces deux derniers restent des détails d'implémentation locaux qui alimentent le nouveau graphe via l'ingestion, sans être remplacés.
2. **Vocabulaire de relations** — `cabinet_knowledge.ontology.RelationType` est étendu de façon additive (nouveaux membres), jamais remplacé par un second vocabulaire.
3. **Portée de la traçabilité** — `ai_governance.provenance`/`.traceability`/`.audit` restent scopés aux productions IA (brouillons) ; la traçabilité du graphe de connaissances passe par `cabinet_knowledge.lineage`, déjà scopée aux `KnowledgeObject` — deux besoins voisins, deux mécanismes distincts et volontairement non fusionnés (comme documenté au Sprint 24 pour Reasoning Packs vs `legal_reasoning`).
4. **Contexte Copilot** — le Sprint 25 étend `CopilotContext` par un champ optionnel plutôt que de faire du Knowledge Graph une dépendance obligatoire du Context Engine — un copilote peut fonctionner sans graphe, le graphe l'enrichit quand disponible.

## Conclusion

Le développement peut commencer. La portée réelle du sprint est
resserrée par cet audit à : un moteur de graphe fédérateur
(`graph_core`), une couche sémantique fine au-dessus de l'embedding
déjà existant (`semantic_engine`), un moteur de résolution d'entités
généralisant un patron déjà présent (`entity_resolution`), un
pipeline d'ingestion orchestrant des moteurs existants
(`ingestion`), une extension légère du Context Engine du Sprint 24
(`copilot_bridge`), et des extensions ciblées de la gouvernance, de
la qualité et de l'observabilité déjà en place.
