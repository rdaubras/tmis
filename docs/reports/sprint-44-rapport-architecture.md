# Rapport d'architecture — Sprint 44 (Réconciliation des trois mécanismes de marketplace)

## Résumé

Suite directe de `docs/171-audit-marketplace.md` (Sprint 43). Trois
livrables de code, une suppression, quatre documents mis à jour :

1. **`CopilotEngine.activate`/`.deactivate`** recâblés sur
   `platform_sdk.extensions.ExtensionEngine`/`business_platform.
   marketplace_subscriptions.MarketplaceSubscriptionEngine` — plus de
   second store d'activation.
2. **`CopilotActivation`** devient une vue recalculée depuis
   l'`ExtensionInstance` du firm, jamais un enregistrement persisté.
3. **Champ `license: str`** sur `CopilotManifest`/`CopilotSpec`,
   remplaçant `_LICENSE = "proprietary"` codé en dur dans
   `copilot/marketplace.py`.
4. **`ai_team.marketplace`** (`MarketplaceListing`) supprimé purement et
   simplement (aucun appelant externe trouvé — voir
   `docs/reports/sprint-44-rapport-audit.md` §4).
5. Docs : `docs/171-audit-marketplace.md` (écart §4 marqué résolu),
   `docs/144-guide-marketplace-legal-copilot-framework.md`.

**Rupture de compatibilité contrôlée, comme autorisé explicitement par ce
sprint** (contrairement au Sprint 43) : `POST /legal-copilots/{id}/install`
et `POST /.../deactivate` gagnent un effet de bord et un nouveau code
d'échec possible. Détail complet ci-dessous, avant/après.

## Décision structurante : `CopilotActivation` devient une vue, pas un store

Avant ce sprint, `CopilotEngine` possédait son propre
`CopilotActivationStorePort`/`InMemoryCopilotActivationStore`
(`(firm_id, copilot_id) -> CopilotActivation`), écrit indépendamment de
`platform_sdk.extensions.ExtensionInstance`. C'est exactement l'écart
documenté par l'audit : un copilote pouvait être « actif » sans jamais
être « installé » ni « facturé ».

Ce store est supprimé (`copilot/ports.py`, `copilot/store.py`) — il n'y a
plus de second enregistrement à garder synchronisé. `CopilotEngine`
compose désormais directement deux mécanismes déjà éprouvés :

```python
# copilot/engine.py
class CopilotEngine:
    def __init__(
        self,
        store: CopilotStorePort,
        registry: CopilotRegistry,
        plugin_registry: PluginRegistryPort,
        publishing: PublishingEngine,
        extensions: ExtensionEngine,
        subscriptions: MarketplaceSubscriptionEngine,
    ) -> None: ...

    def activate(self, firm_id: str, copilot_id: str, actor: str) -> CopilotActivation:
        copilot = self.get(copilot_id)
        self._ensure_published(copilot, actor)
        requested_permissions = frozenset(ExtensionPermission(p) for p in copilot.permissions)
        self._subscriptions.subscribe(
            firm_id, copilot_id, requested_permissions=requested_permissions
        )
        return self._require_activation(firm_id, copilot_id)

    def deactivate(self, firm_id: str, copilot_id: str) -> CopilotActivation:
        self._subscriptions.unsubscribe(firm_id, copilot_id)
        return self._require_activation(firm_id, copilot_id)
```

`CopilotActivation` (lecture) est reconstruite à chaque appel depuis
l'`ExtensionInstance` du firm — `version`, `granted_permissions` et statut
proviennent désormais de la source unique déjà éprouvée :

```python
def _to_activation(instance: ExtensionInstance) -> CopilotActivation:
    return CopilotActivation(
        firm_id=instance.firm_id,
        copilot_id=instance.plugin_id,
        active=instance.status is ExtensionStatus.ACTIVE,
        version=instance.version,
        granted_permissions=frozenset(p.value for p in instance.granted_permissions),
        updated_at=instance.updated_at,
    )
```

`is_active`/`active_copilots` filtrent désormais
`extensions.list_for_firm(firm_id)` plutôt que de lire un store propre —
même source de vérité, aucune duplication d'état.

Ni `ExtensionEngine` ni `MarketplaceSubscriptionEngine` n'ont été modifiés
— confirmé en Phase 0 (`docs/reports/sprint-44-rapport-audit.md` §2)
qu'ils pouvaient porter un `copilot_id` comme `plugin_id` sans changement
de contrat. `CopilotEngine` ne fait que les composer, exactement la
recommandation de `docs/171-audit-marketplace.md`.

### Toujours `subscribe`, jamais `install` directement

`activate` appelle systématiquement `MarketplaceSubscriptionEngine.
subscribe` (jamais `ExtensionEngine.install` directement), avec
`monthly_price_usd` implicite à `0.0` : `CopilotManifest` ne porte
aujourd'hui aucun signal « payant » (hors périmètre de ce sprint — aucune
refonte du modèle de pricing), donc il n'y a pas de base pour brancher sur
l'un ou l'autre. `subscribe` gère déjà nativement un prix nul (aucune
facture créée, `engine.py:48-57`) : router systématiquement par
`subscribe` donne à chaque copilote un `ExtensionSubscription` et un
`LicenseGrant` réels dès aujourd'hui, prêts pour qu'un sprint futur y
attache un prix sans changer ce site d'appel.

## Rupture documentée : `POST /legal-copilots/{id}/install`

### Forme JSON : additive, pas cassante

Requête inchangée (`{"firm_id", "user_id"}`). Réponse : deux champs
ajoutés, aucun retiré ni renommé.

| Champ | Avant | Après |
|---|---|---|
| `firm_id` | ✓ | ✓ (inchangé) |
| `copilot_id` | ✓ | ✓ (inchangé) |
| `active` | ✓ | ✓ (inchangé) |
| `updated_at` | ✓ | ✓ (inchangé) |
| `version` | absent | ajouté — version de l'`ExtensionInstance` installée |
| `granted_permissions` | absent | ajouté — permissions accordées, calculées depuis `ExtensionPermission` |

### Comportement : rupture réelle, pas seulement de forme

**Avant.** `CopilotEngine.activate` écrivait directement dans son propre
store. Précondition unique : le copilote doit exister
(`CopilotEngine.get`). Aucun effet sur `platform_sdk.plugin_registry`.

**Après.** `activate` exige un `PluginManifest` `PUBLISHED` pour installer
(contrat inchangé d'`ExtensionEngine.install`). S'il n'existe pas encore,
`activate` le publie lui-même, de façon idempotente :

```python
def _ensure_published(self, copilot: LegalCopilot, actor: str) -> None:
    manifest = self._plugin_registry.get(copilot.id)
    if manifest is None:
        copilot_manifest = self._registry.get_latest(copilot.id)
        manifest = to_plugin_manifest(copilot, copilot_manifest)
        self._plugin_registry.register(manifest)
    if manifest.status is PublishingStatus.DEVELOPMENT:
        manifest = self._publishing.validate_manifest(copilot.id, actor)
    if manifest.status is PublishingStatus.VALIDATED:
        manifest = self._publishing.sign_manifest(copilot.id, actor)
    if manifest.status is PublishingStatus.SIGNED:
        self._publishing.publish(copilot.id, actor)
```

Conséquences observables :

- **Un appel à `/install` peut désormais échouer pour une raison
  nouvelle** : si `PluginValidator.validate` rejette le manifeste généré
  (dépendance introuvable, permission hors du vocabulaire
  `ExtensionPermission`, etc.), `activate` lève
  `ValidationFailedError` — propagée en 500 par le routeur actuel (aucun
  handler dédié n'existait, ni n'était nécessaire avant ce sprint). Non
  observé sur les 5 copilotes MVP ni sur les fixtures de test existantes
  (permissions et dépendances déjà conformes), mais réel pour un futur
  copilote mal formé. Documenté ici plutôt que silencieusement laissé
  comme un 500 non expliqué.
- **`/install` acquiert un effet de bord de gouvernance** : la première
  activation, par n'importe quel cabinet, publie le copilote pour *tous*
  les cabinets (le `PluginManifest` est un catalogue global, pas
  par-firme). `payload.user_id` de ce premier appelant devient l'`actor`
  de l'historique de publication (`PublishingEvent`). Avant ce sprint,
  seul un appel explicite à `POST /publish-to-marketplace` produisait cet
  effet global.
- **`POST /.../deactivate` sur un couple `(firm_id, copilot_id)` jamais
  installé répond désormais 404** au lieu de 200 avec
  `{"active": false}` : `MarketplaceSubscriptionEngine.unsubscribe` exige
  une souscription existante (`_require`, `engine.py:82-86`) et lève
  `KeyError`, que le routeur traduit en 404
  (`api/routes.py::deactivate_copilot`). Aucun test existant n'exerçait ce
  cas (tous les tests de désactivation désactivent un copilote qu'ils
  viennent d'installer) ; documenté ici comme le comportement délibéré du
  nouveau câblage plutôt que laissé comme un 500 non géré.

Ces trois points sont le prix, assumé par ce sprint, de composer sur les
deux mécanismes déjà éprouvés plutôt que de maintenir un second état — la
recommandation explicite de `docs/171-audit-marketplace.md`.

## Licence : champ réel plutôt que constante figée

`CopilotManifest.license: str = "proprietary"` (même défaut qu'avant, pour
ne rien changer silencieusement pour les copilotes existants) et
`CopilotSpec.license: str = "proprietary"`, threadés à travers
`CopilotBuilder.build` et `POST /legal-copilots/register`
(`license` optionnel, défaut inchangé). `copilot.marketplace.
to_plugin_manifest` lit désormais `manifest.license` au lieu de la
constante de module `_LICENSE`, qui est supprimée.

Portée volontairement minimale, conformément au périmètre du sprint :
aucun champ de prix, aucune refonte du modèle de licence — juste de quoi
qu'un copilote porte une licence qui lui est propre plutôt qu'une valeur
figée pour tous, prérequis pour qu'un futur sprint puisse différencier des
copilotes payants sans nouvelle migration de schéma.

## Suppression de `ai_team.marketplace`

Confirmé en Phase 0 (`docs/reports/sprint-44-rapport-audit.md` §4) :
aucun appelant en dehors du module lui-même. Supprimés :
`ai_team/marketplace/` (4 fichiers), son câblage mort dans
`ai_team/bootstrap.py` (`get_marketplace_catalog`), et son test unitaire
dédié (`tests/unit/ai_team/test_ai_team_marketplace.py`). Aucun plan de
dépréciation nécessaire — pas de code de production à faire migrer.

## Tests adaptés

| Fichier | Changement |
|---|---|
| `tests/unit/legal_copilot_framework/test_copilot_engine.py` | Fixture reconstruite avec les vrais `ExtensionEngine`/`MarketplaceSubscriptionEngine`/`PublishingEngine` (in-memory) au lieu du store d'activation supprimé ; nouveau test couvrant `version`/`granted_permissions` sur la vue |
| `tests/unit/legal_copilot_framework/test_sdk_builder.py` | Même reconstruction de fixture (le constructeur de `CopilotEngine` a changé), aucune assertion métier modifiée |
| `tests/integration/legal_copilot_framework/test_legal_copilot_framework_demo_copilots.py` | `activate(firm_id, copilot_id, actor)` — nouvel argument `actor` obligatoire |

`tests/integration/legal_copilot_framework/test_legal_copilot_framework_api.py`
et `tests/contracts/test_copilot_manage_permission_contract.py` n'ont **pas**
été modifiés — le premier continue de passer parce que le flux
`register → install` qu'il exerce reste observable-identique (publication
transparente), le second parce qu'il n'exerce jamais `/install`.

## Résultat des vérifications

- Suite complète (`pytest -q`, depuis `backend/`) : **2246 passed, 7
  skipped** (référence Sprint 43 : 2258 tests collectés ; -5 net ici — 6
  tests supprimés avec `ai_team.marketplace`, +1 nouveau test sur
  `CopilotEngine.activate` couvrant `version`/`granted_permissions`).
  Aucune régression.
- Couverture (`pytest --cov=tmis`) : **96 %** global, inchangé par
  rapport à la référence — `copilot/engine.py` (99 %, seule ligne non
  couverte : la garde défensive `_require_activation` sur une instance
  absente, invariant garanti par `subscribe`/`unsubscribe` en amont),
  `copilot/marketplace.py`/`copilot/schemas.py`/`registry/schemas.py`
  (100 %).
- `ruff check src tests` → All checks passed.
- `mypy src` (`--strict`) → Success: no issues found in 1895 source
  files.
- `tests/contracts/test_copilot_manage_permission_contract.py` passe
  sans aucune modification, conformément à la Definition of Done.
