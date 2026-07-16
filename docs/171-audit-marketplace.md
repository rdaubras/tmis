# Audit — trois mécanismes de marketplace (Sprint 43)

> Audit seul, conformément au périmètre du Sprint 43 : aucune fusion de
> code n'est faite ici. Recensement factuel + recommandation pour
> arbitrage avec l'utilisateur avant un sprint futur dédié. Voir
> `docs/reports/sprint-43-rapport-audit.md` §4 pour le résumé et
> `docs/144-guide-marketplace-legal-copilot-framework.md`/
> `docs/reports/sprint-24-rapport-audit.md` pour le diagnostic d'origine
> (Sprint 24), que cet audit confirme et complète.

## Contexte

Trois mécanismes coexistent depuis le Sprint 24, chacun dans un bounded
context différent :

1. **`platform_sdk.marketplace`** (Sprint 13) — découverte/catalogue
   générique de plugins publiés.
2. **`business_platform.marketplace_subscriptions`** (Sprint 20) —
   abonnement payant à un plugin publié, wrapper commercial autour du
   premier.
3. **`legal_copilot_framework`** (Sprint 24) — `PluginType.COPILOT`,
   publication d'un copilote comme plugin, **et** activation par cabinet
   d'un copilote (`CopilotEngine.activate`), un mécanisme distinct des
   deux premiers.

L'audit du Sprint 24 avait déjà diagnostiqué ce chevauchement sans le
résoudre, pour ne pas bloquer ce sprint sur un sujet hors périmètre
(`docs/reports/sprint-24-rapport-audit.md`, section « Conflits
d'architecture identifiés »). Un quatrième module, `ai_team.marketplace`
(`MarketplaceListing`), existe également mais est confirmé **mort/non
câblé** : aucun appelant en dehors de son propre bootstrap
(`ai_team/bootstrap.py:13,51`), cohérent avec sa description dans
`docs/144-guide-marketplace-legal-copilot-framework.md` (« jamais câblé
à aucun appelant »). Il est mentionné ci-dessous pour mémoire mais hors
du triptyque principal audité.

## Tableau 1 — Modèle de données / catalogue

| | `platform_sdk.marketplace` | `business_platform.marketplace_subscriptions` | `legal_copilot_framework` (copilot layer) |
|---|---|---|---|
| Entité catalogue | `PluginManifest` (`platform_sdk/plugin_system/schemas.py:33-51`) — id choisi par l'auteur, un seul par id, statut `PublishingStatus` (DEVELOPMENT→VALIDATED→SIGNED→PUBLISHED→RETIRED) | Aucune entité catalogue propre — référence `PluginManifest.id` via `plugin_id` | `LegalCopilot` (objet runtime assemblé) + `CopilotManifest` (`legal_copilot_framework/registry/schemas.py:8-26`, versionné, historique conservé) |
| Schéma d'id | `plugin_id` (chaîne libre choisie par l'auteur) | même `plugin_id`, plus son propre `extsub-{uuid12}` | `copilot_id` propre ; devient un `plugin_id` seulement après le pont `to_plugin_manifest` (mapping identité) |
| Découverte | `MarketplaceEngine.search`/`categories` (filtre `PUBLISHED` uniquement) | Aucune — délègue entièrement à `platform_sdk.marketplace` | Aucune découverte propre — publication uniquement |

## Tableau 2 — Cycle de vie (installation/activation par cabinet)

| | `platform_sdk.extensions` | `business_platform.marketplace_subscriptions` | `legal_copilot_framework` (copilot layer) |
|---|---|---|---|
| Entité d'activation | `ExtensionInstance` (`ext-{uuid4}`, statut ACTIVE/DISABLED/UNINSTALLED, `granted_permissions`, `version`) | `ExtensionSubscription` (`extsub-{uuid12}`, statut ACTIVE/CANCELLED), **enveloppe** un `ExtensionInstance` (appelle `MarketplaceEngine.install`/`.uninstall` directement) | `CopilotActivation` — pas d'id propre (clé `(firm_id, copilot_id)`), booléen `active` seul, **pas de `version`, pas de `granted_permissions`** |
| Point d'entrée API | `platform_sdk.marketplace` REST (`docs/68-guide-marketplace.md`) | `business_platform` REST (abonnement) | `POST /legal-copilots/{id}/install` → `CopilotEngine.activate` |
| Relation avec le catalogue | Valide que le manifeste est `PUBLISHED` avant d'installer | Délègue la validation à `MarketplaceEngine.install` | **Aucune** — n'appelle ni `ExtensionEngine.install` ni `MarketplaceSubscriptionEngine.subscribe` |

**Écart structurel confirmé (non documenté avant cet audit) :** l'activation
d'un copilote par un cabinet ne passe par aucun des deux autres
mécanismes. Un copilote peut donc être « activé »
(`CopilotActivation.active = True`) sans jamais être « installé »
(`ExtensionInstance`) ni « souscrit/facturé » (`ExtensionSubscription`),
et réciproquement. Grep confirmé : `CopilotEngine.activate`/
`CopilotActivation` ne sont référencés nulle part en dehors de
`legal_copilot_framework` lui-même — aucun appelant ne relie les deux
mondes.

## Tableau 3 — Facturation

| | `platform_sdk` | `business_platform.marketplace_subscriptions` | `legal_copilot_framework` (copilot layer) |
|---|---|---|---|
| Concept de prix/facturation | Aucun | `monthly_price_usd`, `LicenseGrant` (type API), factures via `cabinet_os.billing.BillingEngine` | **Aucun** — `_LICENSE = "proprietary"` codé en dur dans `copilot/marketplace.py:5-8`, avec un commentaire explicite : aucun champ `LegalCopilot.license` n'existe encore, « chaque copilote est propriétaire tant qu'un modèle de licence n'est pas conçu » |

## Ce qui est déjà réconcilié

Deux ponts réels et câblés existent, confirmés par lecture directe :

1. `MarketplaceSubscriptionEngine.subscribe`/`unsubscribe`
   (`business_platform/marketplace_subscriptions/engine.py:46,70`)
   appellent directement `MarketplaceEngine.install`/`.uninstall` — la
   facturation n'introduit jamais de second chemin d'installation.
2. `to_plugin_manifest` (`legal_copilot_framework/copilot/marketplace.py:
   11-29`) + `publish_copilot_to_marketplace`
   (`legal_copilot_framework/bootstrap.py:156-169`), exposé via
   `POST /legal-copilots/{id}/publish-to-marketplace` — un copilote
   publié devient un `PluginManifest` réel dans le registre partagé.

Ce qui **n'est pas** réconcilié, et qui n'était pas documenté avant cet
audit : l'activation par cabinet (le troisième axe du Tableau 2).

## Recommandation

**Ne pas fusionner dans ce sprint** (hors périmètre explicite du Sprint
43) — mais le proposer comme sujet d'un sprint dédié futur, pour la
raison suivante : combler l'écart d'activation nécessiterait de choisir
un seul modèle d'activation/version/permission et d'y migrer celui des
deux qui perd (`CopilotActivation` est structurellement plus pauvre —
pas de `version`, pas de `granted_permissions` — qu'`ExtensionInstance`),
et d'introduire un concept de licence/prix dans la couche copilote qui
n'existe pas aujourd'hui. C'est une rupture de compatibilité potentielle
sur `POST /legal-copilots/{id}/install`, exactement le type de
changement le Sprint 43 exclut explicitement.

Proposition pour ce sprint futur (à trancher avec l'utilisateur avant de
commencer, sur le même principe que ce sprint) : faire de
`CopilotEngine.activate` un appelant de
`ExtensionEngine.install`/`MarketplaceSubscriptionEngine.subscribe`
plutôt que de dupliquer leur état — `CopilotActivation` deviendrait alors
une vue en lecture, dérivée de l'`ExtensionInstance` correspondant,
plutôt qu'un second enregistrement à synchroniser manuellement. Ceci
donnerait à la couche copilote la facturation et la gestion de
permissions déjà éprouvées des deux autres mécanismes sans réinventer
l'un ou l'autre — cohérent avec la préférence du dépôt pour composer sur
l'existant plutôt que dupliquer (voir `docs/151-architecture-
persistance.md`).

Le quatrième module mort, `ai_team.marketplace`, devrait être supprimé
purement et simplement lors de ce futur sprint plutôt que réconcilié :
aucun appelant ne le référence, il n'a jamais été qu'un vocabulaire
(`PlanTier` SOLO/CABINET/ENTERPRISE) additionnel et incompatible avec
celui de `business_platform.plans` (`PlanName` TRIAL/BASIC/
PROFESSIONAL/BUSINESS/ENTERPRISE).
