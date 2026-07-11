# Rapport d'architecture — Sprint 13 (TMIS Platform SDK & Marketplace)

## Résumé

Le Sprint 13 ajoute `backend/src/tmis/platform_sdk/` (19 sous-modules
+ une couche API) au-dessus du socle existant. Aucun module métier
des Sprints 2-12 n'a été modifié ; seuls `tmis/api/v1/router.py`
(branchement du routeur) et `tmis/core/config.py` (ajout du réglage
`plugin_signing_key`, sur le même modèle que `license_signing_key`,
Sprint 10) ont été touchés hors `platform_sdk/`.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID / API First** : chaque module
  suit le patron `schemas.py` → `ports.py` (si persistance dédiée) →
  implémentation(s) → composition dans `platform_sdk/bootstrap.py`,
  identique aux sprints précédents.
- **Contrat unique, cinq SDK spécialisés** : `sdk.ports.PluginPort`
  (`id`, `plugin_type`, `invoke()`) est tout ce que
  `sandbox`/`plugin_loader` connaissent d'un plugin — chaque
  `*_sdk` fournit une classe de base ergonomique par type qui adapte
  sa méthode métier (`run`, `fetch_page`, `render_section`) vers cet
  unique point d'entrée.
- **Aucune exécution dynamique de code** : vérifié architecturalement
  — `plugin_loader.PluginImplementationRegistry` n'accepte que des
  classes déjà importées (import Python ordinaire), et
  `workflow_sdk` va plus loin en rendant un workflow entièrement
  déclaratif (`WorkflowCondition` interprétée par un `match` fermé sur
  6 opérateurs, `action` résolue par nom dans un registre fermé) —
  aucun `eval`/`exec` nulle part dans le module.

## Décision structurante : deux cycles de vie distincts

Le manifeste d'un plugin (`PluginManifest.status`,
`tmis.platform_sdk.publishing`) et son installation par cabinet
(`ExtensionInstance.status`, `tmis.platform_sdk.extensions`) sont deux
machines à états séparées — même principe que
`Playbook`/`PlaybookInstance` au Sprint 12. Le premier est global au
catalogue (`DEVELOPMENT → VALIDATED → SIGNED → PUBLISHED → RETIRED`),
le second est scopé par `firm_id` (`ACTIVE`/`DISABLED`/`UNINSTALLED`).
Confondre les deux aurait empêché plusieurs cabinets d'installer
indépendamment le même plugin publié.

## Décision structurante : sandbox logique, pas d'isolation système

Le sprint demande un "sandbox" avec limitation des permissions, accès
contrôlé aux API, quotas de ressources et journalisation.
`SandboxExecutor` implémente exactement ces quatre garanties — mais
volontairement **pas** d'isolation processus/conteneur par plugin :
TMIS exécute uniquement du code Python déjà importé au démarrage
(jamais uploadé ni évalué dynamiquement), donc une isolation système
par plugin serait un theâtre de sécurité sans réel gain tant qu'aucun
mécanisme de chargement de code tiers n'existe. Documenté explicitement
dans docs/65-architecture-platform-sdk.md et dans le docstring de
`SandboxExecutor`.

## Bug trouvé et corrigé pendant le développement

`SandboxExecutor.execute()` exigeait initialement un
`required_permission` obligatoire. En écrivant l'exemple "Workflow
Validation" (qui ne déclare légitimement aucune permission), aucun
appel n'aurait jamais pu réussir : le contrôle de permission aurait
toujours échoué puisqu'aucune permission n'est jamais accordée pour ce
plugin. **Corrigé** en rendant `required_permission: ExtensionPermission
| None = None` — le contrôle n'est appliqué que si une permission est
effectivement exigée par l'appelant. Un test d'intégration dédié
(`test_sandbox_executes_workflow_validation_with_no_required_permission`)
fige ce comportement.

## Réutilisation explicite des sprints précédents

- `tmis.platform.licensing.signing.LicenseKeySigner` (Sprint 10) —
  signature des manifestes, sans nouveau schéma HMAC.
- `tmis.ai_team.agents.ports.KernelPort` (Sprint 11) — `agent_sdk`
  donne accès au Kernel par le même port étroit que `tmis.ai_team`.
- `tmis.ai.cache.ports.CachePort`/`InMemoryCache` (Sprint 2) —
  `connector_sdk` réutilise l'abstraction de cache existante.
- `tmis.legal_drafting.templates.schemas.DocumentType` (Sprint 7) —
  référencé par `document_sdk`.
- Convention `Event`/`EventBus` propre par contexte borné (établie par
  `tmis.collaboration` au Sprint 8) — suivie par `events_sdk`.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 934 fichiers
source (contre 856 avant ce sprint). `pytest` : **1169 tests passés, 4
ignorés** (contre 1068 avant ce sprint) — 101 tests dédiés à
`platform_sdk` (86 unitaires + 15 d'intégration), couverture globale
95,72 %, sans qu'aucun des 1068 tests précédents n'ait été modifié.

## Voir aussi

`docs/65-architecture-platform-sdk.md` pour les diagrammes Mermaid
détaillés (cycle de vie de publication, séquence d'exécution en
sandbox).
