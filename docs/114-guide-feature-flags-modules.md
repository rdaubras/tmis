# Guide — Feature flags et modules (Sprint 20)

## Feature flags — quatre dimensions supplémentaires

`platform.feature_flags.FeatureFlagEngine` (Sprint 10) gère déjà
kill switch, allow-list firm/user, allow-list plan, et rollout
progressif. `feature_flags.BusinessFeatureFlagEngine` **compose** ce
moteur — il ne le réimplémente jamais — et ajoute les quatre
dimensions que le sprint demande : environnement, groupe, fenêtre
temporelle, expérimentation, via `BusinessFlagExtras` (clé partagée
avec le `FeatureFlag` de base).

```python
from tmis.business_platform.bootstrap import get_business_feature_flag_engine
from tmis.business_platform.feature_flags.schemas import BusinessFlagContext, Environment

flags = get_business_feature_flag_engine()
context = BusinessFlagContext(firm_id=firm_id, environment=Environment.STAGING)
if flags.is_enabled("my-feature", context):
    ...
```

Une clé doit passer **à la fois** l'évaluation du moteur de base
**et** chaque dimension `BusinessFlagExtras` présente pour cette clé.
Un flag jamais configuré est **fermé par défaut** (aucune allow-list,
rollout à 0 %) — brancher un flag neuf sur un endpoint existant sans
le semer ouvert casserait donc tout appelant existant ; voir
docs/116-guide-migration-business-platform.md pour le patron « semé
ouvert » utilisé sur l'endpoint de `cabinet_knowledge`.

## Modules — activation par bounded context

`modules.schemas.TmisModule` énumère les 16 bounded contexts de TMIS.
`modules.ModuleRegistry.is_available` compare le module à
`Plan.features` via une table de correspondance
(`_MODULE_FEATURE_MAPPING`) — un module absent de cette table
(`cabinet_os`, `cabinet_knowledge`, `identity_platform`) est
**foundational** : toujours disponible, jamais gaté commercialement.

```python
from tmis.business_platform.bootstrap import get_module_registry
from tmis.business_platform.modules.schemas import TmisModule

modules = get_module_registry()
modules.activate(firm_id, TmisModule.WORKFLOW_AUTOMATION)  # ModuleNotAvailableError si le plan ne l'inclut pas
modules.deactivate(firm_id, TmisModule.WORKFLOW_AUTOMATION)
modules.is_active(firm_id, TmisModule.WORKFLOW_AUTOMATION)  # override explicite, sinon défaut du plan
```

Un `ModuleActivation` explicite (via `activate`/`deactivate`)
surclasse toujours le défaut dérivé du plan pour ce cabinet
spécifiquement — un cabinet peut désactiver un module que son plan
inclut sans affecter les autres cabinets sur le même plan.

## Voir aussi

docs/111-architecture-business-platform.md,
docs/47-guide-securite-entreprise.md (Sprint 10 — Feature Flags).
