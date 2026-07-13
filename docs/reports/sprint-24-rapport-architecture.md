# Rapport d'architecture — Sprint 24 (Legal Copilot Framework)

## Résumé

Le Sprint 24 ajoute `backend/src/tmis/legal_copilot_framework/` (11
sous-modules, 14 endpoints REST, 78 tests dédiés). Le prompt
utilisateur exigeait une Phase 1 d'audit exhaustif avant toute
implémentation ; cet audit (docs/reports/sprint-24-rapport-audit.md)
a directement déterminé la portée : composer 18 composants existants,
étendre 5 enums/schémas de façon additive, et construire seulement 11
composants réellement nouveaux — le SDK, le Registry et les packs
eux-mêmes.

Points de contact hors `legal_copilot_framework/` :

- `tmis/identity_platform/permissions/schemas.py` — ajout de
  `Permission.COPILOT_MANAGE`.
- `tmis/identity_platform/rbac/schemas.py` — `COPILOT_MANAGE`
  accordé aux rôles `PARTNER` et `IT_ADMIN` dans
  `DEFAULT_ROLE_PERMISSIONS` (sans cette étape, tout endpoint mutateur
  du framework aurait toujours répondu 403 — corrigé pendant la
  rédaction des tests d'intégration).
- `tmis/ai_governance/policy_engine/schemas.py` et `engine.py` —
  nouveau `GovernancePolicyType.RESTRICTED_TO_ROLE`, champs
  `required_role`/`user_role` additifs, nouvelle branche dans
  `PolicyEngine.evaluate()`.
- `tmis/platform_sdk/plugin_system/schemas.py` — nouveau
  `PluginType.COPILOT`.
- `tmis/platform_sdk/templates/engine.py` — nouveau stub JSON
  `copilot.json` pour ce type de plugin (jamais un stub `.py`, pour
  ne pas faire importer `legal_copilot_framework` par `platform_sdk`,
  qui se situe plus bas dans le graphe de dépendances).
- `tmis/cloud_operations/metrics/schemas.py` et `engine.py` — cinq
  nouvelles catégories `MetricCategory` (`COPILOT_USAGE`, `AI_COST`,
  `VALIDATION_RATE`, `PACK_REUSE`, `SATISFACTION`) et leur mapping
  vers `MetricKind`.
- `tmis/business_platform/modules/schemas.py` et `engine.py` —
  nouveau `TmisModule.LEGAL_COPILOT_FRAMEWORK`, pour que le bounded
  context dans son ensemble reste activable/plan-gated comme les 16
  autres, sans confondre cette activation-là avec l'activation
  *par copilote* (voir « Conflits d'architecture » ci-dessous).
- `tmis/api/v1/router.py` — montage de
  `legal_copilot_framework_router` sous `/api/v1`.

## Conformité aux principes architecturaux

- **Phase 1 obligatoire avant code** : un rapport d'audit dédié
  (docs/reports/sprint-24-rapport-audit.md) a précédé toute
  implémentation, comme l'exigeait le prompt du sprint lui-même.
- **Composer, ne jamais reconstruire** : dix compositions explicites
  documentées dans docs/139, vers des moteurs des Sprints 2, 6, 7, 11,
  12, 13, 14, 15, 17, 19, 21. Aucun registre de prompts, espace de
  connaissance, moteur de raisonnement, registre de templates,
  bibliothèque de workflows, moteur de politiques ou contexte tenant
  n'est reconstruit.
- **Le patron « pointeur, pas payload »** (nouveau ce sprint) : chaque
  schéma de Pack (`PromptPack`, `KnowledgePack`, `ReasoningPack`,
  `DocumentPack`, `WorkflowPack`) ne stocke que des *ids* référençant
  des entités déjà gérées par un moteur antérieur, résolus fraîchement
  à chaque appel — jamais de copie de contenu.
- **Déclaration vs. exécution** : `ReasoningPack` déclare des
  stratégies et pointe vers des `ReasoningPattern` stockés ; il
  n'exécute jamais un raisonnement — cela reste entièrement la
  responsabilité de `tmis.legal_reasoning` (Sprint 6).
- **Event Driven Architecture** : aucune nouvelle infrastructure
  d'événements ; les compositions au-dessus de `ai_governance`/
  `workflow_automation` restent événementielles via leurs moteurs
  sous-jacents.
- **Multi-tenant strict** : chaque appel touchant l'état d'un cabinet
  passe un `firm_id` jusqu'à `KnowledgeSpace`/`TenantContextEngine`,
  qui appliquent déjà `require_same_firm` (Sprint 10/19).
- **Enterprise Identity & Trust Platform obligatoire** : chaque
  endpoint mutateur de `legal_copilot_framework/api/routes.py` appelle
  `identity_platform.api.guard.authorize_or_403` avec le nouveau
  `Permission.COPILOT_MANAGE`.

## Conflits d'architecture — rappel et confirmation

L'audit (docs/reports/sprint-24-rapport-audit.md) avait anticipé
quatre zones de recouvrement apparent ; l'implémentation les a
confirmées sans déviation :

1. **Activation par copilote ≠ activation par module.**
   `business_platform.modules.ModuleRegistry` active des bounded
   contexts entiers par cabinet (dont, désormais,
   `LEGAL_COPILOT_FRAMEWORK` lui-même) ; `legal_copilot_framework.
   copilot.CopilotEngine.activate/deactivate` active des *produits*
   individuels au sein de ce bounded context. Les deux mécanismes
   coexistent délibérément.
2. **Reasoning Packs restent des déclarations.** L'exécution réelle
   d'une stratégie de raisonnement passe toujours par
   `tmis.legal_reasoning`, jamais par `reasoning_packs`.
3. **Trois couches de marketplace, pas de quatrième.**
   `PluginType.COPILOT` a été ajouté à `platform_sdk.plugin_system`
   plutôt que de construire un mécanisme de catalogue séparé — voir
   docs/144-guide-marketplace-legal-copilot-framework.md pour le
   détail du pont `to_plugin_manifest`/`publish_copilot_to_marketplace`.
4. **Context Engine ne couple pas à `case_intelligence`.**
   `case_context`/`pieces` restent des paramètres fournis par
   l'appelant plutôt que résolus automatiquement — limite de portée
   assumée et documentée dans docs/143.

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `prompt_packs.PromptPackEngine` | `ai.prompts.PromptRegistry` (S2), `ai_fabric.prompt_optimizer` (S14) | stockage/versionnage/rendu de prompt |
| `knowledge_packs.KnowledgePackEngine` | `cabinet_knowledge.knowledge.KnowledgeSpace` (S12) | stockage/gouvernance de connaissance |
| `reasoning_packs.ReasoningPackEngine` | `cabinet_knowledge.reasoning_patterns` (S12) | exécution de raisonnement (reste `legal_reasoning`, S6) |
| `document_packs.DocumentPackEngine` | `legal_drafting.templates.TemplateRegistry` (S7), `cabinet_knowledge.templates` (S12) | structure/sections/variables de document |
| `workflow_packs.WorkflowPackEngine` | `workflow_automation.template_library.TemplateLibrary` (S17) | moteur de workflow |
| `validation_policies.ValidationPolicyEngine` | `ai_governance.policy_engine` + `.human_validation` (S15) | évaluation de politique, validation humaine |
| `context_engine.ContextEngine` | `identity_platform.tenant_context` (S19), `cabinet_knowledge.writing_style` (S12), `ai_governance.policy_engine` (S15) | profil tenant, préférences rédactionnelles, politiques |
| `sdk.CopilotBuilder` | `ai_team.teams.TeamBuilder` (S11) | composition d'équipe d'agents |
| `metrics.CopilotMetricsEngine` | `cloud_operations.metrics.MetricsEngine` (S21) | stockage de métriques historisées |
| `copilot.marketplace.to_plugin_manifest` | `platform_sdk.plugin_system`/`.publishing`/`.marketplace` (S13) | cycle de publication, catalogue, avis, installation |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` → Success, 1801 fichiers source (aucune erreur)
- `pytest -q` → 1903 passed, 4 skipped (1825 tests précédents + 78
  nouveaux : 60 unitaires, 18 intégration)

## Corrections apportées pendant la vérification

- `platform_sdk/templates/engine.py::_COPILOT_STUB` manquait une
  annotation de type (`dict[str, object]`) — révélé par `mypy src`
  après l'ajout du scaffold `PluginType.COPILOT`, corrigé
  immédiatement.
- `identity_platform/rbac/schemas.py` n'accordait `COPILOT_MANAGE` à
  aucun rôle — chaque endpoint mutateur aurait toujours répondu 403.
  Découvert en écrivant les tests d'intégration API, corrigé avant
  de committer.
- Un test d'intégration `platform_sdk` (`test_platform_sdk_lifecycle_
  integration.py`) asserait une égalité exacte de l'ensemble des
  plugins enregistrés dans le registre partagé (`@lru_cache`) —
  fragile dès qu'un autre module publie un plugin dans le même
  process. Assoupli en `>=` (sous-ensemble attendu) plutôt que `==`,
  puisque le partage de singletons `@lru_cache` process-wide entre
  suites de tests est le patron déjà établi dans tout le dépôt.
