# Guide des Plugins (Sprint 13)

## Le manifeste

Chaque plugin possède un `PluginManifest` — la seule source de
vérité sur son identité :

| Champ | Rôle |
|---|---|
| `id` | identifiant unique et stable |
| `name`, `description` | libellés lisibles |
| `version` | chaîne libre, bumpée par le développeur |
| `plugin_type` | `agent` / `connector` / `workflow` / `document_template` / `tool` |
| `author` | auteur ou éditeur |
| `license` | licence du plugin |
| `permissions` | ensemble fermé de `ExtensionPermission` déclarées |
| `dependencies` | identifiants d'autres plugins requis |
| `compatibility` | plage de compatibilité avec le SDK |
| `signature` | apposée à l'étape "signature" du cycle de vie |
| `status` | `development` / `validated` / `signed` / `published` / `retired` |

## Permissions

Le moteur de permissions (`tmis.platform_sdk.permissions`) déclare un
vocabulaire **fermé** — un plugin ne peut jamais inventer une
permission :

```python
class ExtensionPermission(StrEnum):
    READ_CASES = "read_cases"
    READ_DOCUMENTS = "read_documents"
    CREATE_DRAFTS = "create_drafts"
    ACCESS_RESEARCH = "access_research"
    ACCESS_KNOWLEDGE = "access_knowledge"
    MANAGE_USERS = "manage_users"
```

Une permission inconnue dans `manifest.permissions` est un motif de
rejet en validation (voir ci-dessous). À l'installation
(`tmis.platform_sdk.extensions.ExtensionEngine.install`), le cabinet
ne peut accorder que des permissions parmi celles **déclarées** dans
le manifeste — jamais plus.

## Cycle de vie de publication

```
DEVELOPMENT → VALIDATED → SIGNED → PUBLISHED → RETIRED
```

Chaque transition est appliquée par
`tmis.platform_sdk.publishing.PublishingEngine` et historisée
(`PublishingEvent` : de quel statut, vers quel statut, par qui,
pourquoi, quand) — jamais de saut d'étape (`DEVELOPMENT → PUBLISHED`
directement lève `InvalidPublishingTransitionError`).

- **Validation** (`validate_manifest`) — échoue et refuse la
  transition si `PluginValidator.validate()` remonte au moins un
  problème (conformité, permissions inconnues, dépendance manquante ou
  circulaire, incompatibilité de version).
- **Signature** (`sign_manifest`) — appose une signature HMAC-SHA256
  (`tmis.platform.licensing.signing.LicenseKeySigner`, réutilisé du
  Sprint 10) sur `f"{id}:{version}:{author}"`.
- **Publication** (`publish`) — rend le plugin visible dans la
  Marketplace et installable.
- **Retrait** (`retire`) — statut terminal ; un plugin retiré ne peut
  plus être republié (il faudrait un nouveau manifeste).

## Le Sandbox

Voir docs/65-architecture-platform-sdk.md pour le diagramme de
séquence complet. En résumé : chaque exécution passe par
`tmis.platform_sdk.sandbox.SandboxExecutor.execute()`, qui vérifie la
permission requise (si spécifiée), applique un quota d'appels par
minute glissant, charge le plugin (refuse tout ce qui n'est pas
`PUBLISHED`), l'exécute avec un timeout, et journalise
systématiquement le résultat — succès ou échec, un plugin qui lève une
exception ne fait jamais planter l'appelant.

## Bonnes pratiques

- **Ne déclarer que les permissions réellement utilisées par le
  plugin** — chaque permission supplémentaire est une surface
  d'attaque inutile pour le cabinet qui installe le plugin, et
  `ExtensionEngine.install` refusera de toute façon d'accorder une
  permission non déclarée.
- **Ne jamais coder en dur un accès à un module TMIS** — passer
  exclusivement par `PluginContext` (voir docs/67-guide-sdk.md).
- **Documenter les dépendances** dans `manifest.dependencies` plutôt
  que de supposer qu'un autre plugin est déjà installé.
- **Tester avec `required_permission=None`** si le plugin ne nécessite
  aucune permission (voir l'exemple `workflow-validation`).
