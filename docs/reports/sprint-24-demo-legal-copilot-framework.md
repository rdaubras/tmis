# Démonstration — Legal Copilot Framework (Sprint 24)

## Objectif

Ce rapport démontre, avec des sorties réellement capturées (aucune
donnée inventée après coup), les cinq copilotes MVP du sprint et le
cycle de vie complet d'un copilote : construction, résolution des
packs, activation, métriques, publication au Marketplace. Toutes les
données (nom du cabinet, dossier, contenu des connaissances) sont
fictives, conformément à la consigne du sprint.

## Scénario 1 — Seed des cinq copilotes MVP

```
=== Seeding the 5 MVP copilots (fictional data) ===
 - copilot-contentieux
 - copilot-droit-societes
 - copilot-droit-fiscal
 - copilot-droit-social
 - copilot-contrats
```

Chaque copilote publie, avant sa construction, un Prompt Pack, un
Knowledge Pack (avec un `KnowledgeObject` réellement créé dans
`cabinet_knowledge.knowledge.KnowledgeSpace`, visible dans les logs
`cabinet_knowledge.enriched` ci-dessous), un Reasoning Pack, un
Document Pack et un Workflow Pack, puis une Validation Policy — avant
d'appeler `CopilotBuilder.build(spec)`.

```
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=playbook          firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=reasoning_pattern firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=best_practice     firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=reasoning_pattern firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=internal_rule     firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=reasoning_pattern firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=checklist         firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=reasoning_pattern firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=clause            firm_id=demo-firm
2026-07-13 07:37:13 [info] cabinet_knowledge.enriched  type=reasoning_pattern firm_id=demo-firm
```

Dix objets de connaissance réels (un playbook/bonne pratique/règle
interne/checklist/clause par copilote, plus un pattern de raisonnement
par copilote) — chaque log provient du `KnowledgeSpace.create`
existant du Sprint 12, jamais d'un mécanisme de stockage propre au
framework.

## Scénario 2 — Architecture du Copilote Contentieux, agent par agent

```
=== Copilote Contentieux — architecture demonstration ===
domain: civil | status: draft | team_id: df9456f4-5e26-4579-ad8c-3705227cdc79
manifest: copilot-contentieux 1.0.0 draft tmis-legal-copilot-framework

rendered system prompt: Tu es le copilote Contentieux du cabinet Cabinet Demo.
Analyse le dossier D-2026-042, qualifie juridiquement les faits et identifie
les risques.

knowledge pack resolves to: ['Playbook qualification des faits en contentieux']

reasoning pack resolves to pattern: Argumentation contradictoire en contentieux
contractuel | strategy: Opposer systématiquement les arguments des deux
parties avant conclusion.

document pack resolves to templates: ['assignation', 'conclusions', 'memoire']

workflow pack instantiated: ["Préparation d'une audience"]
```

Chaque ligne ci-dessus est produite par un moteur d'un sprint
antérieur, jamais par le framework lui-même :

- `team_id` : un `Team` réel créé par `ai_team.teams.TeamBuilder`
  (Sprint 11).
- Le prompt système est rendu via `ai.prompts.PromptRegistry.get(...).
  render(**kwargs)` (Sprint 2), après résolution de l'override du
  Prompt Pack.
- Le pattern de raisonnement est résolu depuis un `KnowledgeObject`
  réel via `cabinet_knowledge.reasoning_patterns.
  pattern_from_knowledge_object` (Sprint 12) — la stratégie déclarée
  (`CONTRADICTORY_ARGUMENTATION`) n'est jamais exécutée ici, seulement
  référencée.
- Les modèles documentaires (`assignation`, `conclusions`, `memoire`)
  sont les structures réelles de `legal_drafting.templates.
  TemplateRegistry` (Sprint 7), pas des copies.
- Le workflow instancié (« Préparation d'une audience ») est un
  `Workflow` normal, produit par `workflow_automation.
  template_library.TemplateLibrary.instantiate` (Sprint 17).

## Scénario 3 — Installation et activation pour un cabinet

```
=== Activation (installer) for a firm ===
activation: CopilotActivation(firm_id='demo-firm', copilot_id='copilot-contentieux',
active=True, updated_at=...)
active copilots for firm: ['copilot-contentieux']
```

## Scénario 4 — Consultation des métriques

```
=== Metrics (consulter les métriques) ===
CopilotMetricsSnapshot(copilot_id='copilot-contentieux', usage_count=1,
total_ai_cost_usd=0.045, avg_response_time_ms=620.0, validation_rate=1.0,
pack_reuse_count=0, satisfaction_score=None)
```

`satisfaction_score` reste `None` tant qu'aucun retour utilisateur
n'est explicitement enregistré — le modèle est prévu, comme demandé
par le sprint, sans source de données réelle inventée.

## Scénario 5 — Publication au Marketplace

```
=== Publish to Marketplace (préparer un futur Marketplace) ===
platform_sdk.publishing_transition  from_status=development to_status=validated
platform_sdk.publishing_transition  from_status=validated   to_status=signed
platform_sdk.publishing_transition  from_status=signed      to_status=published
plugin_id: copilot-contentieux | plugin_type: copilot | status: published | signed: True
```

Le copilote traverse le cycle de publication `platform_sdk.publishing`
(Sprint 13) sans aucune modification de ce module — développement →
validation → signature → publication — et devient immédiatement
cherchable via `platform_sdk.marketplace.MarketplaceEngine.search`.

## Scénario 6 — Les cinq copilotes MVP, vue d'ensemble

```
copilot-contentieux      domain=civil        prompt_pack=pp-contentieux   document_pack=dp-contentieux workflow_pack=wp-contentieux validation_policy=vp-contentieux-partner
copilot-droit-societes   domain=commercial   prompt_pack=pp-societes      document_pack=dp-societes    workflow_pack=wp-societes  validation_policy=vp-societes-double
copilot-droit-fiscal     domain=fiscal       prompt_pack=pp-fiscal        document_pack=dp-fiscal      workflow_pack=wp-fiscal    validation_policy=vp-fiscal-confidence
copilot-droit-social     domain=social       prompt_pack=pp-social        document_pack=dp-social      workflow_pack=wp-social    validation_policy=vp-social-review
copilot-contrats         domain=commercial   prompt_pack=pp-contrats      document_pack=dp-contrats    workflow_pack=wp-contrats  validation_policy=vp-contrats-role
```

Chaque copilote démontre une politique de validation différente,
couvrant les cinq types demandés par le sprint : validation associé
(Contentieux), double validation (Droit des sociétés), seuil de
confiance minimum (Droit fiscal), revue humaine obligatoire (Droit
social), restriction par rôle (Contrats).

## Bug réel trouvé et corrigé pendant cette démonstration

La première exécution du Scénario 5 a échoué :

```
tmis.platform_sdk.publishing.schemas.ValidationFailedError:
copilot-contentieux: permissions: permission inconnue : 'copilot.contentieux.use'
```

Les cinq copilotes déclaraient des permissions en chaînes libres
(`"copilot.contentieux.use"`), incompatibles avec le vocabulaire fermé
`platform_sdk.permissions.ExtensionPermission` qu'exige
`PluginValidator._check_permissions` — un vrai défaut de réutilisation
(inventer une grammaire de permission alors qu'un vocabulaire existant
convient). Corrigé en remplaçant ces chaînes par des valeurs réelles
de `ExtensionPermission` (`ACCESS_KNOWLEDGE`, `ACCESS_RESEARCH`,
`CREATE_DRAFTS`, `READ_CASES`, `READ_DOCUMENTS` selon le copilote) dans
les cinq modules `copilots/*.py`. Un second défaut, découvert au même
moment, est documenté dans le rapport d'architecture : `Permission.
COPILOT_MANAGE` n'était accordé à aucun rôle par défaut, ce qui aurait
fait échouer silencieusement tout appel API mutateur.

## Vérification finale après correction

```
$ ruff check src tests
All checks passed!

$ mypy src
Success: no issues found in 1801 source files

$ pytest -q
1903 passed, 4 skipped in 10.83s
```
