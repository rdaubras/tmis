# Guide — Quotas et licences (Sprint 20)

## Les sept dimensions de quota

`quotas.schemas.QuotaDimension` : `USERS`, `STORAGE_GB`, `AI_CALLS`,
`GPU_MINUTES`, `CASES`, `WORKFLOWS`, `AGENTS`. Six dérivent leur
limite de base du plan actif (`PlanLimits`) ; `GPU_MINUTES` n'a aucune
allocation de plan (base toujours zéro — le GPU s'achète en option).

```python
from tmis.business_platform.bootstrap import get_business_quota_engine
from tmis.business_platform.quotas.schemas import QuotaDimension

quotas = get_business_quota_engine()
limit = quotas.limit_for(firm_id, QuotaDimension.WORKFLOWS)
result = quotas.check(firm_id, QuotaDimension.WORKFLOWS, current_usage=used)
if not result.allowed:
    ...  # 429
```

Un override (`set_override(firm_id, dimension, extra_amount)`) est
**toujours additif** sur la limite du plan — jamais un remplacement.
Pour `AI_CALLS` spécifiquement, `check_ai_calls`/`record_ai_call`
composent directement `ai_fabric.quotas.QuotaEngine` (Sprint 14)
plutôt que de réimplémenter un compteur.

`limit_for`/`check_ai_calls` appellent `SubscriptionEngine.get(firm_id)`,
qui lève un `KeyError` si le cabinet n'a pas d'abonnement Business
Platform — un appelant qui veut une dégradation gracieuse (ne pas
bloquer un cabinet non onboardé) doit capturer ce `KeyError`, voir
docs/116-guide-migration-business-platform.md.

## Les quatre types de licence

`licenses.schemas.LicenseType` : `NOMINATIVE` (un siège = un
utilisateur), `FLOATING` (pool partagé, check-out/check-in),
`GUEST` (accès temporaire), `API` (client machine, ex. une extension
Marketplace).

```python
from tmis.business_platform.bootstrap import get_license_engine
from tmis.business_platform.licenses.schemas import LicenseType

licenses = get_license_engine()
grant = licenses.assign(firm_id, LicenseType.NOMINATIVE, holder_id=user_id)
licenses.revoke(firm_id, grant.id)
new_grant = licenses.transfer(firm_id, grant.id, new_holder_id=other_user_id)
```

`transfer` ne mute jamais une licence existante : il révoque
l'ancienne et émet une nouvelle licence (`transferred_from` référence
l'ancien grant) — chaque clé signée reste immuable une fois émise.
Les licences flottantes passent par `set_floating_pool_capacity` puis
`checkout_floating`/`checkin_floating`, qui lèvent
`FloatingPoolExhaustedError` une fois le pool saturé.

Chaque licence est signée par `platform.licensing.signing.
LicenseKeySigner` (Sprint 10) — le même signataire que
`platform.licensing.LicenseEngine`, garantissant que toute clé émise
dans le système, qu'elle soit au niveau cabinet ou par détenteur,
utilise le même secret HMAC.

## Voir aussi

docs/111-architecture-business-platform.md,
docs/47-guide-securite-entreprise.md (Sprint 10 — Licensing/Quotas).
