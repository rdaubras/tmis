# Rapport d'audit initial — Sprint 24 (Legal Copilot Framework)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint. Il recense, par lecture directe du code (jamais
par déduction depuis les noms), ce qui existe déjà dans les dix
composants que le prompt demande de réutiliser, et détermine ce qui
manque réellement.

## Composants réutilisés tels quels

| Composant existant | Ce qu'il fournit déjà | Usage dans le LCF |
|---|---|---|
| `ai_team.registry.AgentDescriptor`/`AgentRegistryPort` | Manifeste d'agent versionné (skills, coût, modèles compatibles) | Déclaration des agents d'un copilote — aucun second modèle d'agent |
| `ai_team.teams.TeamBuilder.build_custom_team` | Composition d'une équipe à partir d'une liste d'agents arbitraire | Construit l'équipe IA d'un copilote |
| `ai.prompts.PromptRegistry` | Registre de prompts versionné, historique complet conservé | Stockage/versionnage de tout prompt référencé par un Prompt Pack |
| `ai_fabric.prompt_optimizer.PromptOptimizer` | Adaptation d'un prompt à la fenêtre de contexte d'un modèle | Rendu d'un prompt de pack adapté au modèle cible |
| `cabinet_knowledge.knowledge.KnowledgeSpace` | Stockage générique tenant-scopé de tout artefact de connaissance (playbook, clause, pattern, style rédactionnel...), gouvernance intégrée | Résolution des objets référencés par un Knowledge Pack |
| `cabinet_knowledge.reasoning_patterns.ReasoningPattern` | Vue typée d'un `KnowledgeObject(type=REASONING_PATTERN)` | Les stratégies déclarées par un Reasoning Pack |
| `legal_reasoning` (orchestrateur + ports) | Moteurs d'exécution du raisonnement (qualification, arguments, contre-arguments, confiance, conflits) | Exécution réelle des stratégies déclarées ; jamais reconstruit |
| `legal_drafting.templates.TemplateRegistry`/`DocumentTemplate` | Structure documentaire versionnée (9 types), sections, variables, règles, contrôles | Vérité structurelle référencée par un Document Pack |
| `cabinet_knowledge.templates.CabinetTemplate` | Personnalisation par cabinet d'un type de document, gouvernée | Surcharge par cabinet référencée par un Document Pack |
| `workflow_automation.template_library.WorkflowTemplate`/`TemplateLibrary` | Modèle de workflow publiable et instanciable, personnalisable | Primitive directe d'un Workflow Pack — `instantiate()` produit toujours un `Workflow` normal |
| `identity_platform.api.guard.authorize_or_403` | Point d'entrée unique vers l'autorisation centrale | Appelé avant toute action privilégiée du LCF (Registry, activation) |
| `identity_platform.tenant_context`/`platform.security.tenant_isolation` | Isolation multi-tenant canonique (`TenantContext`, `require_same_firm`) | Base du Context Engine, jamais réimplémentée |
| `ai_governance.policy_engine.PolicyEngine` | Politiques par cabinet (validation avant export, seuil de confiance, relecture obligatoire...) | Base des Validation Policies |
| `ai_governance.human_validation.HumanValidationEngine` | Validation simple/multiple/hiérarchique, historisée | Exécution des Validation Policies de type validation humaine |
| `platform_sdk.plugin_system.PluginManifest`/`plugin_registry`/`marketplace`/`sandbox` | Manifeste, permissions, installation, exécution sandboxée déjà génériques | Modèle de packaging/distribution réutilisé pour la future Marketplace de copilotes |
| `business_platform.marketplace_subscriptions.MarketplaceSubscriptionEngine` | Abonnement + licence + facturation sur une installation `platform_sdk` | Réutilisé tel quel pour la commercialisation d'un copilote, jamais reconstruit |
| `cloud_operations.metrics.MetricsEngine` | Historisation de métriques par catégorie, labels libres | Toutes les métriques copilote — aucun second entrepôt de métriques |
| `runtime_platform.event_streaming.EventEnvelope` | Ordonnancement/idempotence/versionnage pour tout bus existant | Disponible pour les événements de publication de version (non utilisé de façon centrale dans ce sprint — noté comme extension future) |

## Composants étendus (changement additif, aucune rupture)

| Composant | Extension apportée | Pourquoi une extension et non un nouveau composant |
|---|---|---|
| `identity_platform.permissions.Permission` | Ajout de `COPILOT_MANAGE` | Un seul vocabulaire de permissions cross-module doit exister |
| `ai_governance.policy_engine.GovernancePolicyType` | Ajout de `RESTRICTED_TO_ROLE` + champ `required_role` sur `GovernancePolicy`/`PolicyEvaluationContext` | La restriction par rôle est un cas de politique de gouvernance, pas un concept séparé |
| `platform_sdk.plugin_system.PluginType` | Ajout de `COPILOT` | Un copilote publiable est un type de plugin parmi d'autres, pas un second système de manifeste |
| `cloud_operations.metrics.MetricCategory` | Ajout de `COPILOT_USAGE`, `AI_COST`, `VALIDATION_RATE`, `PACK_REUSE`, `SATISFACTION` | Extension additive du même entrepôt, jamais un second |
| `business_platform.modules.TmisModule` | Ajout de `LEGAL_COPILOT_FRAMEWORK` | Le LCF est un bounded context activable/désactivable par cabinet comme les 16 existants |

## Composants réellement nouveaux (aucun équivalent trouvé)

| Nouveau composant | Justification |
|---|---|
| `legal_copilot_framework.copilot` (schéma `LegalCopilot` + moteur) | Aucun concept d'assemblage cross-pack n'existe ailleurs — c'est la couche d'orchestration demandée |
| `legal_copilot_framework.sdk` (`CopilotSpec` + `CopilotBuilder`) | Aucun SDK de déclaration de copilote n'existe |
| `legal_copilot_framework.registry` (`CopilotManifest`, historique de versions) | `platform_sdk.plugin_registry` ne modélise pas domaine/auteur/compatibilité spécifiques à un copilote ; **construit sur le même patron** que `legal_drafting.templates.TemplateRegistry` (historique complet, `get_latest`) plutôt qu'un patron inédit |
| `legal_copilot_framework.context_engine` | Aucun agrégateur cross-contexte (utilisateur+cabinet+dossier+connaissances+politiques+préférences) n'existe |
| `legal_copilot_framework.prompt_packs` | `PromptRegistry` ne modélise ni héritage ni surcharge — couche fine ajoutée par-dessus |
| `legal_copilot_framework.knowledge_packs` | Aucune notion de « sélection nommée et versionnée » d'objets de connaissance n'existe |
| `legal_copilot_framework.reasoning_packs` | Aucune déclaration de stratégie de raisonnement référençant des patterns n'existe |
| `legal_copilot_framework.document_packs` | Aucune composition Document Template + Cabinet Template n'existe encore |
| `legal_copilot_framework.workflow_packs` | Couche fine : un Workflow Pack est un ensemble nommé d'ids `WorkflowTemplate`, instancié via `TemplateLibrary.instantiate` |
| `legal_copilot_framework.validation_policies` | Aucune déclaration de politique *spécifique à un copilote* n'existe (les politiques `ai_governance` sont par cabinet, pas par copilote) |
| `legal_copilot_framework.metrics` | Aucun agrégat de métriques *par copilote* n'existe |

## Conflits d'architecture identifiés — et comment ils sont évités

1. **Trois couches de marketplace déjà existantes** (`platform_sdk.marketplace`,
   `business_platform.marketplace_subscriptions`, `ai_team.marketplace`).
   Décision : ne **pas** créer une quatrième couche. Un copilote publiable
   devient un `PluginManifest(plugin_type=COPILOT)` — installation, mise
   à jour, dépendances et licences restent gérées par les deux premières
   couches. `ai_team.marketplace` (agents seuls, jamais câblé à
   `platform_sdk`) n'est pas touché — hors périmètre de ce sprint.
2. **Deux systèmes de "template" déjà existants** (`legal_drafting.
   templates` structurel vs. `cabinet_knowledge.templates` personnalisation
   par cabinet). Décision : le Document Pack compose les deux, ne
   fusionne ni ne duplique aucun des deux schémas.
3. **Deux notions de "reasoning pattern"** (artefact de connaissance
   stocké vs. moteurs d'exécution `legal_reasoning`). Décision : le
   Reasoning Pack reste une déclaration (référence des patterns stockés)
   ; l'exécution reste entièrement dans `legal_reasoning`, jamais
   dupliquée.
4. **`business_platform.modules.TmisModule` active des bounded contexts
   entiers, pas des produits individuels.** Décision : l'activation
   *par copilote* (activer "Contentieux" sans activer "Droit fiscal")
   reste une responsabilité propre au LCF (`copilot.engine`), tandis que
   l'activation du LCF *dans son ensemble* pour un cabinet suit le
   patron `TmisModule` existant — les deux notions sont concomitantes,
   pas redondantes.

## Conclusion

Le développement peut commencer : chaque phase du sprint a un point de
composition identifié vers un composant existant, et les cinq
extensions additives listées ci-dessus sont suffisantes — aucun
nouveau composant proposé ne duplique une capacité déjà présente dans
le dépôt.
