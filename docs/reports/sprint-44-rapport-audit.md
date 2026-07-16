# Rapport d'audit — Sprint 44 (Réconciliation des trois mécanismes de marketplace)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Audit obligatoire »). Il confirme, par
lecture directe du dépôt, les quatre prémisses listées dans le brief, et
documente un cinquième point — non listé dans le brief, mais découvert en
vérifiant la faisabilité concrète du recâblage — tranché avec
l'utilisateur avant tout code, sur le même principe que les Sprints 26-28,
37 et 43.

## 1. Appelants réels de `CopilotEngine.activate`/`CopilotActivation`

Grep confirmé (`CopilotEngine|CopilotActivation` sur tout `backend/`) : 11
fichiers, tous internes à `legal_copilot_framework` ou à ses tests. Aucun
appelant externe au bounded context.

| Appelant | Fichier:ligne | Usage |
|---|---|---|
| `POST /{copilot_id}/install` | `api/routes.py:185-196` | `engine.activate(firm_id, copilot_id)` |
| `POST /{copilot_id}/deactivate` | `api/routes.py:199-207` | `engine.deactivate(firm_id, copilot_id)` |
| `get_copilot_engine()` | `bootstrap.py` | Construction du singleton process |
| `test_copilot_engine.py` | `tests/unit/legal_copilot_framework/` | Tests unitaires de l'engine |
| `test_sdk_builder.py` | `tests/unit/legal_copilot_framework/` | Construit `CopilotEngine` pour tester `CopilotBuilder` (n'appelle jamais `activate`) |
| `test_legal_copilot_framework_demo_copilots.py` | `tests/integration/legal_copilot_framework/` | `copilot_engine.activate(firm_id, "copilot-contentieux")` |
| `test_legal_copilot_framework_api.py` | `tests/integration/legal_copilot_framework/` | `POST /install` puis `POST /deactivate` bout-en-bout |
| `tests/contracts/test_copilot_manage_permission_contract.py` | — | N'exerce que `POST /register`, jamais `/install`/`/deactivate` |

Surface de rupture mesurée : deux endpoints REST, un site de construction
(bootstrap), et trois fichiers de test unitaires/intégration à adapter au
nouveau constructeur de `CopilotEngine`. Le test de contrat RBAC du
Sprint 43 n'est pas concerné : il n'exerce jamais `/install`.

## 2. Forme de `ExtensionInstance` et `MarketplaceSubscriptionEngine.subscribe`

Les deux portent bien un `plugin_id: str` libre — confirmé qu'un
`copilot_id` peut y transiter sans aucune modification de leur contrat :

- `ExtensionInstance` (`platform_sdk/extensions/schemas.py:19-34`) :
  `id, firm_id, plugin_id, version, granted_permissions
  (frozenset[ExtensionPermission]), status, installed_at, updated_at`.
  Structurellement plus riche que l'ancien `CopilotActivation` (version,
  permissions accordées, id propre) — exactement le diagnostic de
  `docs/171-audit-marketplace.md` §Tableau 2.
- `MarketplaceSubscriptionEngine.subscribe(firm_id, plugin_id, *,
  requested_permissions=frozenset(), monthly_price_usd=0.0)`
  (`business_platform/marketplace_subscriptions/engine.py:38-66`) : appelle
  `MarketplaceEngine.install` (donc `ExtensionEngine.install`) puis
  `LicenseEngine.assign` et, seulement si `monthly_price_usd > 0`, facture
  via `BillingEngine`. Un prix nul est un chemin de code déjà géré
  nativement (pas de facture créée), pas un cas particulier à ajouter.

**Point non listé dans le brief, trouvé en vérifiant la faisabilité, pas
supposé :** `ExtensionEngine.install` (`platform_sdk/extensions/engine.py:
44-57`) exige que le `plugin_id` corresponde à un `PluginManifest` déjà au
statut `PUBLISHED` dans `platform_sdk.plugin_registry`, sinon
`PluginNotAvailableError`. Or `CopilotEngine.activate` n'a aujourd'hui
**aucune** précondition de ce type : `test_install_then_deactivate_copilot`
(`test_legal_copilot_framework_api.py:99-127`) et
`test_activating_a_demo_copilot_for_a_firm_makes_it_active`
(`test_legal_copilot_framework_demo_copilots.py:112-122`) appellent
`/install`/`activate()` juste après `register`/`seed`, **sans jamais
publier au marketplace au préalable**. Recâbler `activate` sur
`ExtensionEngine.install` tel quel casse donc ce flux existant.

**Décision arbitrée avec l'utilisateur (avant tout code) :**
`CopilotEngine.activate` publie désormais lui-même le copilote
(`register` + `validate_manifest` + `sign_manifest` + `publish` via
`platform_sdk.publishing.PublishingEngine`) s'il n'est pas déjà
`PUBLISHED`, avant d'installer — de façon idempotente (un copilote déjà
publié explicitement via `POST /publish-to-marketplace` n'est pas
republié). Ceci préserve le comportement observable actuel de
`POST /install` (succès direct après `/register`, aucun test cassé) au
prix d'un effet de bord nouveau et documenté (voir
`docs/reports/sprint-44-rapport-architecture.md`) : `/install` absorbe
désormais une action de gouvernance (publication signée) qui restait
jusqu'ici un acte explicite distinct.

## 3. État du champ licence sur `LegalCopilot`/`CopilotManifest`

Confirmé : `_LICENSE = "proprietary"` (`copilot/marketplace.py:5-8`, avant
ce sprint) était bien une constante de module, jamais un champ de
`LegalCopilot` ni de `CopilotManifest`. Grep exhaustif (`_LICENSE|
proprietary|\.license\b` sur `legal_copilot_framework/src` et ses tests) :
**aucun consommateur ne dépend de cette valeur précise** — ni test, ni
autre module ne lit ou n'assert `"proprietary"`. Remplacement sans risque
de régression silencieuse.

Modèle de licence déjà existant côté `platform_sdk` : `PluginManifest.
license` (`plugin_system/schemas.py:45`) est un simple `str` libre (pas un
enum fermé) — `"MIT"` dans les exemples de plugins
(`platform_sdk/examples/registration.py`), `"proprietary"` pour les
copilotes. `PluginValidator._check_conformity`
(`validation/engine.py:57-58`) exige seulement qu'il soit non vide.
`CopilotManifest.license: str = "proprietary"` reprend donc exactement ce
vocabulaire (un `str` libre), sans en inventer un second.

## 4. Appelants de `ai_team.marketplace`/`MarketplaceListing`

Revérifié, pas supposé, sur le même principe que la correction de
prémisse `COPILOT_MANAGE` du Sprint 43 : grep exhaustif de
`MarketplaceListing|ai_team\.marketplace|InMemoryMarketplaceCatalog` sur
tout `backend/` (hors le module lui-même). Deux occurrences seulement,
**toutes internes au module et à son propre test unitaire** :

- `ai_team/bootstrap.py:13,51` — `get_marketplace_catalog()`, jamais
  appelée ailleurs (grep confirmé : zéro appelant de
  `get_marketplace_catalog` en dehors de sa propre définition).
- `tests/unit/ai_team/test_ai_team_marketplace.py` — teste le module
  directement, ne constitue pas un appelant externe.

Le seul autre hit texte (`MarketplaceListingResponse` dans
`platform_sdk/api/schemas.py`/`routes.py`) est une coïncidence de nommage
sur un schéma Pydantic de `platform_sdk.marketplace` (le catalogue de
plugins, sans rapport avec `ai_team.marketplace.MarketplaceListing`) — pas
un appelant du module audité.

Confirmé également : `MarketplaceListing.subscription_plan_required`
référence `cabinet_os.subscriptions.PlanTier` (SOLO/CABINET/ENTERPRISE),
un vocabulaire de plans distinct et incompatible de
`business_platform.plans.PlanName` (TRIAL/BASIC/PROFESSIONAL/BUSINESS/
ENTERPRISE) — exactement le diagnostic de
`docs/171-audit-marketplace.md`. Suppression pure et simple effectuée
(pas de plan de dépréciation nécessaire, aucun appelant externe trouvé).

## Conclusion

Les quatre prémisses du brief se confirment à la lecture directe du code.
Un cinquième point, non anticipé par le brief mais bloquant pour
l'implémentation (précondition `PUBLISHED` de `ExtensionEngine.install`
incompatible avec le flux `register → install` actuellement testé), a été
identifié et tranché avec l'utilisateur avant tout code (§2) : publication
automatique et idempotente à la première activation. Voir
`docs/reports/sprint-44-rapport-architecture.md` pour l'implémentation et
le détail de la rupture de comportement que cela introduit sur
`POST /legal-copilots/{id}/install`.
